# Code adapted from: https://github.com/aanand/git-up/blob/master/lib/git-up.rb#L162-L181
require 'colored'

def check_bundler
  begin
    require 'bundler'
    ENV['BUNDLE_GEMFILE'] ||= File.expand_path('Gemfile')
    Gem.loaded_specs.clear
    Bundler.setup
  rescue Bundler::GemNotFound, Bundler::GitError
    puts
    print 'Gems are missing. '.yellow

    if ARGV[0] == 'autoinstall'
      puts "Running `bundle install`.".yellow
      system "bundle", "install"
    else
      puts "You should `bundle install`.".yellow
    end
  end
end

check_bundler