# Builds the data for the CV page from the LaTeX source at build time.
#
# The LaTeX file (see `cv_tex` in _config.yml) is the single source of truth for
# the CV. Before Jekyll renders anything, this hook runs cv/build_cv.py, which
# parses the AltaCV macros into JSON, and exposes the result as `site.data.cv`.
# Nothing is written to _data/, so there is no generated file to keep in sync.
#
# If python3 is missing or the parser fails, a warning is logged and the page
# falls back to the download link only.

require "json"
require "open3"

Jekyll::Hooks.register :site, :post_read do |site|
  tex = site.config["cv_tex"] || "cv/cv.tex"
  tex_path = File.join(site.source, tex)
  script = File.join(site.source, "cv", "build_cv.py")

  unless File.exist?(tex_path) && File.exist?(script)
    Jekyll.logger.warn "CV:", "skipping, #{tex} or cv/build_cv.py not found"
    next
  end

  out, err, status = Open3.capture3("python3", script, "--tex", tex_path)
  err.each_line { |l| Jekyll.logger.warn "CV:", l.strip unless l.strip.empty? }

  if status.success?
    site.data["cv"] = JSON.parse(out)
    Jekyll.logger.info "CV:", "built site.data.cv from #{tex}"
  else
    Jekyll.logger.error "CV:", "cv/build_cv.py failed (exit #{status.exitstatus}); the CV page will show the PDF link only"
  end
end
