from conans import ConanFile
from conans import CMake
import os

############### CONFIGURE THESE VALUES ##################
default_user = "bincrafters"
default_channel = "testing"
#########################################################

channel = os.getenv("CONAN_CHANNEL", default_channel)
username = os.getenv("CONAN_USERNAME", default_user)


class DefaultNameConan(ConanFile):
    name = "DefaultName"
    version = "0.1"
    settings = "os", "compiler", "build_type", "arch"
    requires = "sdl2_image/2.0.2@%s/%s" % (username, channel)
    generators = ["cmake"] # Generates conanbuildinfo.gcc with all deps information
    export = ["face.png"]

    def build(self):
        cmake = CMake(self)
        self.run('cmake %s %s' % (self.source_folder, cmake.command_line))
        self.run("cmake --build . %s" % cmake.build_config)

    def imports(self):
        self.copy(pattern="*.dll", dst="bin", src="bin")
        self.copy(pattern="*.dylib", dst="bin", src="lib") #What about .so ? dont we use .rpath or is that uncommon practice for linux?

    def test(self):
        self.run("cd bin && .%sexample" % (os.sep))
