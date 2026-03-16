# Copyright Advanced Micro Devices, Inc.
# SPDX-License-Identifier: MIT

cmake_minimum_required(VERSION 3.20)
project(hecbench_spirv_builder NONE)

find_package(Python3 REQUIRED COMPONENTS Interpreter)

if(NOT DEFINED THEROCK_SOURCE_DIR)
  message(FATAL_ERROR "THEROCK_SOURCE_DIR must be provided")
endif()

set(HECBENCH_SOURCE_DIR "${THEROCK_SOURCE_DIR}/third-party/HeCBench")
set(HECBENCH_OUTPUT_DIR "${CMAKE_CURRENT_BINARY_DIR}/hecbench_spirv_out")
set(HECBENCH_SKIP_BENCHMARKS_FILE
  "${CMAKE_CURRENT_SOURCE_DIR}/hecbench_spirv_skipped_benchmarks.txt"
)
set(HECBENCH_BUILD_ARGS
  "--source-dir" "${HECBENCH_SOURCE_DIR}"
  "--output-dir" "${HECBENCH_OUTPUT_DIR}"
  "--rocm-path" "${THEROCK_ROCM_PATH_HINT}"
  "--skip-benchmarks-file" "${HECBENCH_SKIP_BENCHMARKS_FILE}"
)

if(DEFINED THEROCK_CXX_COMPILER_HINT AND THEROCK_CXX_COMPILER_HINT)
  list(APPEND HECBENCH_BUILD_ARGS
    "--cxx-compiler" "${THEROCK_CXX_COMPILER_HINT}"
  )
endif()

if(DEFINED THEROCK_HIPCC_HINT AND THEROCK_HIPCC_HINT)
  list(APPEND HECBENCH_BUILD_ARGS
    "--hipcc" "${THEROCK_HIPCC_HINT}"
  )
endif()

add_custom_command(
  OUTPUT "${HECBENCH_OUTPUT_DIR}/.built_stamp"
  COMMAND "${CMAKE_COMMAND}" -E rm -rf "${HECBENCH_OUTPUT_DIR}"
  COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/build_hecbench_spirv.py"
          ${HECBENCH_BUILD_ARGS}
  COMMAND "${CMAKE_COMMAND}" -E touch "${HECBENCH_OUTPUT_DIR}/.built_stamp"
  DEPENDS
    "${CMAKE_CURRENT_SOURCE_DIR}/build_hecbench_spirv.py"
    "${HECBENCH_SKIP_BENCHMARKS_FILE}"
  VERBATIM
)

add_custom_target(hecbench_spirv_build ALL
  DEPENDS "${HECBENCH_OUTPUT_DIR}/.built_stamp"
)

install(DIRECTORY "${HECBENCH_OUTPUT_DIR}/src/"
  DESTINATION "libexec/hecbench_spirv/src"
)
