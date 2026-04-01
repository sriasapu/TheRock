# Copyright Advanced Micro Devices, Inc.
# SPDX-License-Identifier: MIT

# HeCBench SPIR-V benchmark builder.
#
# Builds HeCBench HIP benchmarks targeting amdgcnspirv using the amd-hip
# compiler toolchain provided by TheRock.

cmake_minimum_required(VERSION 3.25)
project(hecbench_spirv_builder CXX)

find_package(Python3 REQUIRED COMPONENTS Interpreter)

set(HECBENCH_BASE "${HECBENCH_SOURCE_DIR}")

find_program(HECBENCH_MAKE_EXECUTABLE NAMES gmake make REQUIRED)
set(HECBENCH_MAKE_PARALLEL_LEVEL "$ENV{CMAKE_BUILD_PARALLEL_LEVEL}"
  CACHE STRING "Parallel job count for HeCBench makefile builds; empty uses tool default")
set(_hecbench_make_command "${HECBENCH_MAKE_EXECUTABLE}")
if(HECBENCH_MAKE_PARALLEL_LEVEL)
  list(APPEND _hecbench_make_command "-j${HECBENCH_MAKE_PARALLEL_LEVEL}")
endif()

# ---------------------------------------------------------------------------
# SPIR-V flags (overridable via cmake cache)
# ---------------------------------------------------------------------------
set(HECBENCH_SPIRV_CFLAGS "-x hip --offload-arch=amdgcnspirv -std=c++17 -Wall"
  CACHE STRING "CFLAGS for HeCBench SPIR-V benchmarks")
set(HECBENCH_SPIRV_LDFLAGS "--hip-link --offload-arch=amdgcnspirv"
  CACHE STRING "LDFLAGS for HeCBench SPIR-V benchmarks")

# ---------------------------------------------------------------------------
# Load skip list
# ---------------------------------------------------------------------------
set(_skip_file "${CMAKE_CURRENT_SOURCE_DIR}/hecbench_spirv_skipped_benchmarks.txt")
if(NOT EXISTS "${_skip_file}")
  message(FATAL_ERROR "Skip-benchmarks file not found: ${_skip_file}")
endif()
file(STRINGS "${_skip_file}" _skip_lines)
set(_skipped)
foreach(_line ${_skip_lines})
  string(REGEX REPLACE "#.*$" "" _entry "${_line}")
  string(STRIP "${_entry}" _entry)
  if(_entry)
    list(APPEND _skipped "${_entry}")
  endif()
endforeach()
list(LENGTH _skipped _skip_count)
message(STATUS "HeCBench: ${_skip_count} benchmark(s) in skip list")

# ---------------------------------------------------------------------------
# Discover *-hip benchmark directories
# ---------------------------------------------------------------------------
file(GLOB _all_dirs LIST_DIRECTORIES true "${HECBENCH_BASE}/src/*-hip")
list(SORT _all_dirs)

set(_bench_dirs)
foreach(_dir ${_all_dirs})
  get_filename_component(_name "${_dir}" NAME)
  if(NOT "${_name}" IN_LIST _skipped)
    list(APPEND _bench_dirs "${_dir}")
  endif()
endforeach()

list(LENGTH _bench_dirs _bench_count)
message(STATUS "HeCBench: ${_bench_count} benchmark(s) to build")
if(_bench_count EQUAL 0)
  message(FATAL_ERROR "No *-hip benchmarks to build under ${HECBENCH_BASE}/src")
endif()

set(_fix_script "${CMAKE_CURRENT_SOURCE_DIR}/fix_makefiles.py")
set(_fix_stamp "${CMAKE_CURRENT_BINARY_DIR}/stamps/makefiles_fixed.stamp")

add_custom_command(
  OUTPUT "${_fix_stamp}"
  COMMAND "${CMAKE_COMMAND}" -E make_directory "${CMAKE_CURRENT_BINARY_DIR}/stamps"
  COMMAND "${Python3_EXECUTABLE}" "${_fix_script}" ${_bench_dirs}
  COMMAND "${CMAKE_COMMAND}" -E touch "${_fix_stamp}"
  DEPENDS "${_fix_script}"
  COMMENT "Fixing HeCBench Makefiles: removing $(CFLAGS) from link rules"
  VERBATIM
)
add_custom_target(hecbench_fix_makefiles DEPENDS "${_fix_stamp}")

set(_stamps)
foreach(_dir ${_bench_dirs})
  get_filename_component(_name "${_dir}" NAME)
  set(_stamp "${CMAKE_CURRENT_BINARY_DIR}/stamps/${_name}.built")

  add_custom_command(
    OUTPUT "${_stamp}"
    COMMAND ${_hecbench_make_command}
      "CC=${CMAKE_CXX_COMPILER}"
      "EXTRA_CFLAGS=${HECBENCH_SPIRV_CFLAGS}"
      "LDFLAGS=${HECBENCH_SPIRV_LDFLAGS}"
    COMMAND "${CMAKE_COMMAND}" -E touch "${_stamp}"
    WORKING_DIRECTORY "${_dir}"
    DEPENDS "${_fix_stamp}"
    COMMENT "Building HeCBench SPIR-V: ${_name}"
    VERBATIM
  )
  list(APPEND _stamps "${_stamp}")
endforeach()

add_custom_target(hecbench_spirv_build ALL DEPENDS ${_stamps})

# ---------------------------------------------------------------------------
# Install only the benchmarks that were actually built (not skipped).
# ---------------------------------------------------------------------------
foreach(_dir ${_bench_dirs})
  get_filename_component(_name "${_dir}" NAME)
  install(DIRECTORY "${_dir}/"
    DESTINATION "libexec/hecbench_spirv/src/${_name}"
    USE_SOURCE_PERMISSIONS
    PATTERN ".git" EXCLUDE
  )
endforeach()
