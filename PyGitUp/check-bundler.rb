# Code adapted from: https://github.com/aanand/git-up/blob/master/lib/git-up.rb#L162-L194
begin
  require 'colored'
rescue LoadError
  class String
    def yellow
      self
    end
  end
end

def check_bundler
  begin
    require 'bundler'
    ENV['BUNDLE_GEMFILE'] ||= File.expand_path('Gemfile')
    Gem.loaded_specs.clear
    Bundler.setup
  rescue Bundler::GemNotFound, Bundler::GitError
    puts
    print 'Gems are missing. '.yellow

    if ARGV.include? 'autoinstall'
      if ARGV.include? 'local'
        puts "Running `bundle install --local`.".yellow
        unless system "bundle", "install", "--local"
          puts "Problem running `bundle install --local`. Running `bundle install` instead.".yellow
          system "bundle", "install"
        end
      else
        puts "Running `bundle install`.".yellow
        system "bundle", "install"
      end

      if ARGV.include? 'rbenv'
        puts "Running `rbenv rehash`.".yellow
        system "rbenv", "rehash"
      end
    else
      puts "You should `bundle install`.".yellow
    end

  end
end

check_bundler