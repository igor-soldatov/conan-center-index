from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, replace_in_file
import os


required_conan_version = ">=2.0.9"


class DisruptorCppConan(ConanFile):
    name = "disruptor-cpp"
    description = "C++ port of the LMAX Disruptor"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/Abc-Arbitrage/Disruptor-cpp"
    topics = ("disruptor", "concurrency", "ring-buffer", "lmax")
    package_type = "library"

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    implements = ["auto_shared_fpic"]

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("boost/1.83.0", transitive_headers=True, transitive_libs=True)

    def validate(self):
        check_min_cppstd(self, 14)

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.15 <4]")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        root_cmake_lists = os.path.join(self.source_folder, "CMakeLists.txt")
        replace_in_file(
            self,
            root_cmake_lists,
            "project(Disruptor)\ncmake_minimum_required(VERSION 2.6)",
            "cmake_minimum_required(VERSION 2.6)\nproject(Disruptor)",
        )

        cmake_lists = os.path.join(self.source_folder, "Disruptor", "CMakeLists.txt")
        replace_in_file(
            self,
            cmake_lists,
            "include_directories(\"..\")\n\n",
            "include_directories(\"..\")\n\n"
            "option(DISRUPTOR_BUILD_SHARED \"Build shared library\" ON)\n"
            "option(DISRUPTOR_BUILD_STATIC \"Build static library\" ON)\n\n",
        )

        replace_in_file(
            self,
            cmake_lists,
            """add_library(DisruptorShared SHARED ${Disruptor_sources})
target_link_libraries(DisruptorShared ${Boost_LIBRARIES})
set_target_properties(DisruptorShared PROPERTIES OUTPUT_NAME Disruptor)
set_target_properties(DisruptorShared PROPERTIES VERSION ${DISRUPTOR_VERSION})
set_target_properties(DisruptorShared PROPERTIES SOVERSION ${DISRUPTOR_VERSION_MAJOR})

add_library(DisruptorStatic STATIC ${Disruptor_sources})
set_target_properties(DisruptorStatic PROPERTIES OUTPUT_NAME Disruptor)
""",
            """set(disruptor_targets \"\")
if(DISRUPTOR_BUILD_SHARED)
    add_library(DisruptorShared SHARED ${Disruptor_sources})
    target_link_libraries(DisruptorShared ${Boost_LIBRARIES})
    set_target_properties(DisruptorShared PROPERTIES OUTPUT_NAME Disruptor)
    set_target_properties(DisruptorShared PROPERTIES VERSION ${DISRUPTOR_VERSION})
    set_target_properties(DisruptorShared PROPERTIES SOVERSION ${DISRUPTOR_VERSION_MAJOR})
    list(APPEND disruptor_targets DisruptorShared)
endif()

if(DISRUPTOR_BUILD_STATIC)
    add_library(DisruptorStatic STATIC ${Disruptor_sources})
    set_target_properties(DisruptorStatic PROPERTIES OUTPUT_NAME Disruptor)
    list(APPEND disruptor_targets DisruptorStatic)
endif()
""",
        )

        replace_in_file(
            self,
            cmake_lists,
            "install(TARGETS DisruptorShared DisruptorStatic",
            "install(TARGETS ${disruptor_targets}",
        )

        stdafx = os.path.join(self.source_folder, "Disruptor", "stdafx.h")
        replace_in_file(
            self,
            stdafx,
            "#if _MSC_VER // only on Windows\n",
            "#if _MSC_VER // only on Windows\n\n# ifndef NOMINMAX\n#  define NOMINMAX\n# endif\n",
        )
        replace_in_file(
            self,
            stdafx,
            "# include <Windows.h>\n",
            "# include <Windows.h>\n# ifdef max\n#  undef max\n# endif\n# ifdef min\n#  undef min\n# endif\n",
        )

        type_info = os.path.join(self.source_folder, "Disruptor", "TypeInfo.h")
        replace_in_file(
            self,
            type_info,
            "struct hash< Disruptor::TypeInfo > : public unary_function< Disruptor::TypeInfo, size_t >",
            "struct hash< Disruptor::TypeInfo >",
        )

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["DISRUPTOR_BUILD_TESTS"] = False
        tc.cache_variables["DISRUPTOR_BUILD_SHARED"] = self.options.shared
        tc.cache_variables["DISRUPTOR_BUILD_STATIC"] = not self.options.shared
        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("boost", "cmake_file_name", "Boost")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENCE.txt", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["Disruptor"]
        self.cpp_info.set_property("cmake_file_name", "disruptor-cpp")
        self.cpp_info.set_property("cmake_target_name", "disruptor-cpp::disruptor-cpp")
        self.cpp_info.requires = ["boost::system", "boost::thread", "boost::chrono"]
