# frozen_string_literal: true
require "pathname"

def walk_up_until(file_to_find, start_path=nil)
    here = start_path || Dir.pwd
    # if absolute
    if not Pathname.new(here).absolute?
        here = File.join(Dir.pwd, here)
    end
    loop do
        check_path = File.join(here, file_to_find)
        if File.exist?(check_path)
            return check_path
        end
        # reached the top
        if here == File.dirname(here)
            return nil
        # else go up one and try again
        else
            here = File.dirname(here)
        end
    end
end