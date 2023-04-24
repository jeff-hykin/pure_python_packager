# frozen_string_literal: true
require "date"
require 'fileutils'

if ENV["FORNIX_FOLDER"] == nil
    exit 1
end

FileUtils.cd(ENV["FORNIX_FOLDER"])

Gem::Specification.new do |spec|
    spec.name = 'walk_up'
    spec.version = IO.read(ENV["FORNIX_FOLDER"]+"/gem_version.txt")
    spec.date = Date.today.to_s
    spec.summary = 'Find files in parent directories'
    spec.authors = ["Jeff Hykin",]
    spec.homepage = 'https://github.com/jeff-hykin/walk_up.git'
    spec.license = 'MIT'
    spec.description       = <<-desc
        A simple function for walking up a file directory until a certain file is found.

        ```ruby
        require "walk_up"

        require_relative walk_up_until("globals.rb") # <- will keep looking in parent directories for a "globals.rb" file
        ```
    desc
    spec.files = Dir["{lib}/**/*", "LICENSE", "*.md"]
    
    spec.required_ruby_version = '>=2.5.0'

    spec.metadata = {
        "yard.run" => "yri",
    }
end