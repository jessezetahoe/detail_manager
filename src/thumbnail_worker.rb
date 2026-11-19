# frozen_string_literal: true
#
# Detail Manager - LayOut thumbnail render worker
#
# Run from the SketchUp Ruby Console:  load '<program folder>/thumbnail_worker.rb'
# Reads the render queue that Detail Manager prepared, opens each master LayOut
# file READ-ONLY, hides the configured layers (GUIDES) in memory, exports PDF,
# restores the layers and never saves the master.
# Data folder: whichever Detail Manager data folder prepared the newest queue.
#
require 'json'
require 'fileutils'

module ZEDetailManagerPOC07AThumbnailWorker
  extend self

  remove_const(:APP_DIRS) if const_defined?(:APP_DIRS, false)
  # Data folders Detail Manager uses (daily copy, development copy, older builds).
  # The worker takes the one whose render queue was prepared most recently, so it
  # always answers the copy of Detail Manager that asked for the render.
  APP_DIRS = [
    'ZE Detail Manager',
    'ZE Detail Manager Dev',
    'ZE Detail Manager Prototype 0.1',
    'ZE Detail Manager POC 07A'
  ].freeze

  def local_root
    ENV['LOCALAPPDATA'] || ENV['TEMP'] || Dir.home
  end

  def app_root
    @app_root ||= begin
      candidates = APP_DIRS.map { |d| File.join(local_root, d) }
      queued = candidates.select { |d| File.file?(File.join(d, 'thumbnail_jobs', 'queue.json')) }
      queued.empty? ? candidates.first : queued.max_by { |d| File.mtime(File.join(d, 'thumbnail_jobs', 'queue.json')) }
    end
  end

  def queue_path
    File.join(app_root, 'thumbnail_jobs', 'queue.json')
  end

  def exact_layer_matches(doc, requested)
    wanted = requested.map { |x| x.to_s.strip.downcase }.reject(&:empty?)
    doc.layers.to_a.select { |layer| wanted.include?(layer.name.to_s.strip.downcase) }
  end

  def file_mtime_ns(path)
    t = File.mtime(path)
    (t.to_i * 1_000_000_000) + t.nsec
  end

  def render_job(job, hidden_names)
    source = job.fetch('source_layout')
    raise "Source LayOut file not found: #{source}" unless File.file?(source)

    expected_size = job['expected_size_bytes'].to_i
    expected_mtime_ns = job['expected_mtime_ns'].to_i
    actual_size = File.size(source)
    actual_mtime_ns = file_mtime_ns(source)

    if expected_size > 0 && actual_size != expected_size
      raise "Source file size changed after indexing: #{source}"
    end
    if expected_mtime_ns > 0 && actual_mtime_ns != expected_mtime_ns
      raise "Source modified after indexing: #{source}"
    end

    output_dir = job.fetch('output_dir')
    FileUtils.rm_rf(output_dir)
    FileUtils.mkdir_p(output_dir)
    pdf_path = File.join(output_dir, 'render.pdf')
    manifest_path = File.join(output_dir, 'render_manifest.json')

    puts "\nOpening READ-ONLY: #{source}"
    doc = Layout::Document.open(source)
    pages = doc.pages
    layers = exact_layer_matches(doc, hidden_names)

    puts "  Pages: #{pages.length}"
    puts "  Hidden-layer request: #{hidden_names.empty? ? '<none>' : hidden_names.join(', ')}"
    puts "  Matched: #{layers.empty? ? '<none>' : layers.map(&:name).join(', ')}"

    snapshot = []
    begin
      pages.each_with_index do |page, page_index|
        layers.each do |layer|
          begin
            was_visible = page.layer_visible?(layer)
            snapshot << [page, layer, was_visible]
            page.set_layer_visibility(layer, false) if was_visible
          rescue => e
            puts "  WARNING page #{page_index + 1}, layer #{layer.name}: #{e.class}: #{e.message}"
          end
        end
      end

      page_info = doc.page_info
      options = { start_page: 0, end_page: pages.length - 1 }
      puts "  Exporting PDF: #{pdf_path}"
      result = doc.export(pdf_path, options)
      raise "LayOut PDF export returned #{result.inspect}" unless result
      raise "LayOut PDF export did not create #{pdf_path}" unless File.file?(pdf_path)

      manifest = {
        'poc' => '07A',
        'source_layout' => source,
        'layout_filename' => job['layout_filename'],
        'source_key' => job['source_key'],
        'expected_size_bytes' => expected_size,
        'expected_mtime_ns' => expected_mtime_ns,
        'page_width_inches' => page_info.width.to_f,
        'page_height_inches' => page_info.height.to_f,
        'page_count' => pages.length,
        'pdf' => pdf_path,
        'hidden_layers_requested' => hidden_names,
        'hidden_layers_matched' => layers.map(&:name),
        'pages' => pages.each_with_index.map { |p, i|
          { 'index_1based' => i + 1, 'name' => p.name.to_s }
        }
      }
      File.write(manifest_path, JSON.pretty_generate(manifest))
      puts "  Complete: #{(File.size(pdf_path) / 1024.0 / 1024.0).round(2)} MiB"
      true
    ensure
      snapshot.reverse_each do |page, layer, visible|
        begin
          page.set_layer_visibility(layer, visible)
        rescue => e
          puts "  WARNING restoring #{layer.name}: #{e.class}: #{e.message}"
        end
      end
    end
  end

  def run
    @app_root = nil # look again on every run
    qpath = queue_path
    unless File.file?(qpath)
      UI.messagebox(
        "Detail Manager thumbnail queue not found.\n\n" \
        "In Detail Manager, open Library and admin tools and click '1. Prepare Render Queue' first.\n\n" \
        "Expected:\n#{qpath}"
      )
      return
    end

    queue = JSON.parse(File.read(qpath))
    hidden_names = Array(queue['hidden_layers_exact']).map(&:to_s)
    jobs = Array(queue['jobs'])

    if jobs.empty?
      UI.messagebox('The Detail Manager thumbnail queue contains no LayOut files.')
      return
    end

    puts "\n=== DETAIL MANAGER THUMBNAIL WORKER ==="
    puts "Data folder: #{app_root}"
    puts "Queue: #{qpath}"
    puts "Jobs: #{jobs.length}"

    successes = 0
    failures = []

    jobs.each_with_index do |job, index|
      puts "\n[#{index + 1}/#{jobs.length}] #{job['layout_filename']}"
      begin
        successes += 1 if render_job(job, hidden_names)
      rescue => e
        failures << {
          'file' => job['source_layout'],
          'error' => "#{e.class}: #{e.message}"
        }
        puts e.full_message
      end
    end

    status_path = File.join(app_root, 'thumbnail_jobs', 'last_worker_result.json')
    FileUtils.mkdir_p(File.dirname(status_path))
    File.write(status_path, JSON.pretty_generate({
      'completed_at' => Time.now.to_s,
      'successes' => successes,
      'failures' => failures
    }))

    msg = "Detail Manager thumbnail render complete.\n\n#{successes}/#{jobs.length} master file(s) rendered."
    msg += "\n#{failures.length} failed - see Ruby Console." unless failures.empty?
    msg += "\n\nReturn to Detail Manager and click '3. Process Rendered Thumbnails'."
    UI.messagebox(msg)
  rescue => e
    puts e.full_message
    UI.messagebox(
      "Detail Manager thumbnail worker failed:\n\n#{e.class}: #{e.message}\n\n" \
      "See Ruby Console for details."
    )
  end
end

ZEDetailManagerPOC07AThumbnailWorker.run
