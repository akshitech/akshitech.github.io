# frozen_string_literal: true

source "https://rubygems.org"

# Built in GitHub Actions with this Jekyll, not the github-pages gem.
gem "jekyll", "~> 4.4"
gem "webrick" # for `jekyll serve` on Ruby 3+
gem "csv"
gem "base64"
gem "bigdecimal"
gem "logger"

group :jekyll_plugins do
  gem "jekyll-sitemap"
  gem "jekyll-redirect-from"
end

group :test do
  gem "html-proofer", "~> 5.0"
end
