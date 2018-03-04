from conans import ConanFile, CMake, tools, AutoToolsBuildEnvironment
from conans.tools import download, unzip
import shutil
import os


class SDLConan(ConanFile):
    name = "sdl2_image"
    version = "2.0.2"
    description = "sdl2_image is an image file loading library."
    folder = "sdl2_image-%s" % version
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False], "fast_jpg_load": [True, False]}
    default_options = '''shared=False
    fPIC=True
    fast_jpg_load=False'''
    generators = "cmake"
    exports = ["CMakeLists.txt"]
    url = "https://github.com/bincrafters/conan-sdl2_image"
    requires = "sdl2/2.0.7@bincrafters/stable", "libpng/1.6.34@bincrafters/stable", "libjpeg-turbo/1.5.2@bincrafters/stable", "libwebp/0.6.1@bincrafters/stable"
    license = "MIT"
    filename = "SDL2_image-%s" % version
    build_policy = ""

    def config(self):
        del self.settings.compiler.libcxx

    def source(self):
        zip_name = "%s.tar.gz" % self.filename
        download("https://www.libsdl.org/projects/SDL_image/release/%s" % zip_name, zip_name)
        unzip(zip_name)
        os.unlink(zip_name)

    def build(self):
        if self.settings.os == "Windows":
            self.build_cmake()
        else:
            self.build_with_make()

    def build_with_make(self):
        env_build = AutoToolsBuildEnvironment(self)
        if self.options.fPIC:
            env_build.fpic = True
        else:
            env_build.fpic = False

        envvars = env_build.vars

        custom_vars = 'LIBPNG_LIBS= SDL_LIBS= LIBPNG_CFLAGS='
        sdl2_config_path = os.path.join(self.deps_cpp_info["sdl2"].bin_paths[0], "sdl2-config")

        self.run("cd %s" % self.filename)
        self.run("chmod a+x %s/configure" % self.filename)
        self.run("chmod a+x %s" % sdl2_config_path)

        if self.settings.os == "Macos":  # Fix rpath, we want empty rpaths, just pointing to lib file
            old_str = "-install_name \$rpath/"
            new_str = "-install_name "
            tools.replace_in_file("%s/configure" % self.filename, old_str, new_str)

        old_str = '#define LOAD_PNG_DYNAMIC "$png_lib"'
        new_str = ''
        tools.replace_in_file("%s/configure" % self.filename, old_str, new_str)

        old_str = '#define LOAD_JPG_DYNAMIC "$jpg_lib"'
        new_str = ''
        tools.replace_in_file("%s/configure" % self.filename, old_str, new_str)

        old_str = '#define LOAD_WEBP_DYNAMIC "$webp_lib"'
        new_str = ''
        tools.replace_in_file("%s/configure" % self.filename, old_str, new_str)

        with tools.environment_append(envvars):
            configure_command = 'cd %s && SDL2_CONFIG=%s %s ./configure' % (self.filename, sdl2_config_path, custom_vars)
            self.output.warn("Configure with: %s" % configure_command)
            self.run(configure_command)

        old_str = 'DEFS = '
        new_str = 'DEFS = -DLOAD_JPG=1 -DLOAD_PNG=1 -DLOAD_WEBP=1 ' # Trust conaaaan!
        tools.replace_in_file("%s/Makefile" % self.filename, old_str, new_str)

        old_str = '\nLIBS = '
        new_str = '\n# Removed by conan: LIBS2 = '
        tools.replace_in_file("%s/Makefile" % self.filename, old_str, new_str)

        old_str = '\nLIBTOOL = '
        new_str = '\nLIBS = %s \nLIBTOOL = ' % " ".join(["-l%s" % lib for lib in self.deps_cpp_info.libs]) # Trust conaaaan!
        tools.replace_in_file("%s/Makefile" % self.filename, old_str, new_str)

        old_str = '\nLIBPNG_CFLAGS ='
        new_str = '\n# Commented by conan: LIBPNG_CFLAGS ='
        tools.replace_in_file("%s/Makefile" % self.filename, old_str, new_str)

        old_str = '\nLIBPNG_LIBS ='
        new_str = '\n# Commented by conan: LIBPNG_LIBS ='
        tools.replace_in_file("%s/Makefile" % self.filename, old_str, new_str)

        old_str = '\nOBJCFLAGS'
        new_str = '\n# Commented by conan: OBJCFLAGS ='
        tools.replace_in_file("%s/Makefile" % self.filename, old_str, new_str)

        old_str = '\nSDL_CFLAGS ='
        new_str = '\n# Commented by conan: SDL_CFLAGS ='
        tools.replace_in_file("%s/Makefile" % self.filename, old_str, new_str)

        old_str = '\nSDL_LIBS ='
        new_str = '\n# Commented by conan: SDL_LIBS ='
        tools.replace_in_file("%s/Makefile" % self.filename, old_str, new_str)

        old_str = '\nCFLAGS ='
        new_str = '\n# Commented by conan: CFLAGS ='
        tools.replace_in_file("%s/Makefile" % self.filename, old_str, new_str)

        old_str = '\n# Commented by conan: CFLAGS ='
        fpic = "-fPIC"  if self.options.fPIC else ""
        m32 = "-m32" if self.settings.arch == "x86" else ""
        debug = "-g" if self.settings.build_type == "Debug" else "-s -DNDEBUG"
        new_str = '\nCFLAGS =%s %s %s %s\n# Commented by conan: CFLAGS =' % (" ".join(self.deps_cpp_info.cflags), fpic, m32, debug)
        tools.replace_in_file("%s/Makefile" % self.filename, old_str, new_str)

        self.run("cd %s && make" % (self.filename))

    def build_cmake(self):
        shutil.copy("CMakeLists.txt", "%s/CMakeLists.txt" % self.filename)
        cmake = CMake(self)

        args = ["-DLOAD_TIF=0"]  # We do not yet tif image loading

        if self.options.fast_jpg_load:
            args += ["-DFAST_JPG_LOAD"]
        args += ["-DBUILD_SHARED_LIBS=%s" % ("ON" if self.options.shared else "OFF")]
        if self.settings.compiler == "Visual Studio":
            self.options.fPIC = False
        args += ["-DFPIC=%s" % ("ON" if self.options.fPIC else "OFF")]

        self.run("cd %s &&  mkdir build" % self.folder)
        self.run('cd %s/build && cmake .. %s %s' % (self.folder, cmake.command_line, " ".join(args)))
        self.run("cd %s/build && cmake --build . %s" % (self.folder, cmake.build_config))

    def package(self):
        self.copy(pattern="SDL_image.h", dst="include", src="%s" % self.folder, keep_path=False) #TODO: "sdl2" subfolder
        self.copy(pattern="*.lib", dst="lib", src="%s" % self.folder, keep_path=False)

        if not self.options.shared:
            self.copy(pattern="*.a", dst="lib", src="%s" % self.folder, keep_path=False)
        else:
            self.copy(pattern="*.so*", dst="lib", src="%s" % self.folder, keep_path=False)
            self.copy(pattern="*.dylib*", dst="lib", src="%s" % self.folder, keep_path=False)
            self.copy(pattern="*.dll", dst="bin", src="%s" % self.folder, keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ["sdl2_image"]
