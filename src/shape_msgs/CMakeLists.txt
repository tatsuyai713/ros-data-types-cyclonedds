cmake_minimum_required(VERSION 3.18)

project(shape_msgs LANGUAGES CXX VERSION 1.0.0)

# ------------------------------------------------------------
# Compiler / dependencies
# ------------------------------------------------------------
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS  OFF)

add_compile_options(-Wall -Wextra -Wnon-virtual-dtor
                    -Wno-deprecated-declarations -Wno-unused-result)

find_package(Boost REQUIRED)
find_package(CycloneDDS REQUIRED COMPONENTS CXX)
find_package(CycloneDDS-CXX REQUIRED)

# ------------------------------------------------------------
# Output dirs
# ------------------------------------------------------------
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

# ------------------------------------------------------------
# Collect *.idl (any depth)
# ------------------------------------------------------------
file(GLOB_RECURSE ORIGINAL_IDL_FILES "${CMAKE_CURRENT_SOURCE_DIR}/*.idl")

set(GENERATED_SRCS)
set(GENERATED_HDRS)
set(GENERATED_INCLUDE_DIRS)

# ------------------------------------------------------------
# Generate code ONCE ONLY with custom target
# ------------------------------------------------------------
foreach(IDL_FILE IN LISTS ORIGINAL_IDL_FILES)
    get_filename_component(IDL_DIR       "${IDL_FILE}" DIRECTORY)
    get_filename_component(SUBDIR_NAME   "${IDL_DIR}"  NAME)
    get_filename_component(PKG_DIR       "${IDL_DIR}"  DIRECTORY)
    get_filename_component(PKG_NAME      "${PKG_DIR}"  NAME)
    get_filename_component(IDL_BASENAME  "${IDL_FILE}" NAME_WE)

    set(GEN_DIR "${CMAKE_BINARY_DIR}/generated/${PKG_NAME}/${SUBDIR_NAME}")
    set(GEN_CPP "${GEN_DIR}/${IDL_BASENAME}.cpp")
    set(GEN_HPP "${GEN_DIR}/${IDL_BASENAME}.hpp")

    list(APPEND GENERATED_SRCS  "${GEN_CPP}")
    list(APPEND GENERATED_HDRS  "${GEN_HPP}")
    list(APPEND GENERATED_INCLUDE_DIRS
         "${GEN_DIR}"
         "${CMAKE_BINARY_DIR}/generated/${PKG_NAME}")
endforeach()

# Remove duplicates from include dirs
list(REMOVE_DUPLICATES GENERATED_INCLUDE_DIRS)

# ------------------------------------------------------------
# Step 1: Generate all IDL files using custom target (not custom command)
# ------------------------------------------------------------
add_custom_target(shape_msgs_generate_initial
    COMMAND ${CMAKE_COMMAND} -E echo "Generating all IDL files once"
    COMMENT "Initial IDL generation")

foreach(IDL_FILE IN LISTS ORIGINAL_IDL_FILES)
    get_filename_component(IDL_DIR       "${IDL_FILE}" DIRECTORY)
    get_filename_component(SUBDIR_NAME   "${IDL_DIR}"  NAME)
    get_filename_component(PKG_DIR       "${IDL_DIR}"  DIRECTORY)
    get_filename_component(PKG_NAME      "${PKG_DIR}"  NAME)
    get_filename_component(IDL_BASENAME  "${IDL_FILE}" NAME_WE)

    set(GEN_DIR "${CMAKE_BINARY_DIR}/generated/${PKG_NAME}/${SUBDIR_NAME}")
    set(GEN_CPP "${GEN_DIR}/${IDL_BASENAME}.cpp")
    set(GEN_HPP "${GEN_DIR}/${IDL_BASENAME}.hpp")

    # header search paths for idlc
    set(IDL_INC_ARGS
        -I "${PKG_DIR}/msg/"
        -I "${PKG_DIR}/srv/"
        -I "${PKG_DIR}/.."
    )

    add_custom_target(generate_${PKG_NAME}_${SUBDIR_NAME}_${IDL_BASENAME}
        COMMAND ${CMAKE_COMMAND} -E make_directory "${GEN_DIR}"
        COMMAND ${CMAKE_COMMAND} -E chdir "${GEN_DIR}"
                idlc -l cxx -fcase-sensitive
                    ${IDL_INC_ARGS}
                    "${IDL_FILE}"
        COMMAND sed -i "s|return \\\"${PKG_NAME}::${SUBDIR_NAME}::${IDL_BASENAME}\\\";|return \\\"${PKG_NAME}::${SUBDIR_NAME}::dds_::${IDL_BASENAME}_\\\";|g" "${GEN_HPP}"
        DEPENDS "${IDL_FILE}"
        COMMENT "Generating ${IDL_BASENAME}"
        VERBATIM
    )
    
    add_dependencies(shape_msgs_generate_initial generate_${PKG_NAME}_${SUBDIR_NAME}_${IDL_BASENAME})
endforeach()

# ------------------------------------------------------------
# Step 2: Update headers after ALL generation is complete
# ------------------------------------------------------------
add_custom_target(update_headers_target_shape_msgs
    COMMAND ${CMAKE_COMMAND} -E echo "Running update_headers.sh"
    COMMAND ${CMAKE_COMMAND} -E env bash ${CMAKE_BINARY_DIR}/../../scripts/update_headers.sh
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/generated/shape_msgs
    DEPENDS shape_msgs_generate_initial
    COMMENT "Updating header files with CycloneDX C++ compatibility"
    VERBATIM
)

# ------------------------------------------------------------
# Step 3: Create final copies of sources after processing
# ------------------------------------------------------------
set(FINAL_SRCS)
foreach(SRC IN LISTS GENERATED_SRCS)
    get_filename_component(SRC_DIR "${SRC}" DIRECTORY)
    get_filename_component(SRC_NAME "${SRC}" NAME_WE)
    set(FINAL_SRC "${SRC_DIR}/${SRC_NAME}_final.cpp")
    
    add_custom_target(copy_${PROJECT_NAME}_${SRC_NAME}_final
        COMMAND ${CMAKE_COMMAND} -E copy_if_different "${SRC}" "${FINAL_SRC}"
        DEPENDS update_headers_target_shape_msgs
        COMMENT "Creating final copy of ${SRC_NAME}.cpp"
        VERBATIM
    )
    
    list(APPEND FINAL_SRCS "${FINAL_SRC}")
endforeach()

# Create a target that represents all final sources are ready
add_custom_target(final_sources_shape_msgs
    DEPENDS ${FINAL_SRCS}
    COMMENT "All final sources ready")

# Make sure all copy targets are dependencies
foreach(SRC IN LISTS GENERATED_SRCS)
    get_filename_component(SRC_NAME "${SRC}" NAME_WE)
    add_dependencies(final_sources_shape_msgs copy_${PROJECT_NAME}_${SRC_NAME}_final)
endforeach()

# ------------------------------------------------------------
# Step 4: Define source files as existing files (not generated)
# ------------------------------------------------------------
# Create dummy rules for final source files to tell CMake they exist
foreach(FINAL_SRC IN LISTS FINAL_SRCS)
    add_custom_command(
        OUTPUT "${FINAL_SRC}"
        COMMAND ${CMAKE_COMMAND} -E echo "Final source ${FINAL_SRC} ready"
        DEPENDS final_sources_shape_msgs
        COMMENT "Marking ${FINAL_SRC} as ready"
        VERBATIM
    )
endforeach()

# ------------------------------------------------------------
# Step 5: Build library using final sources
# ------------------------------------------------------------
add_library(shape_msgs SHARED ${FINAL_SRCS})
set_target_properties(shape_msgs PROPERTIES LINKER_LANGUAGE CXX)

target_include_directories(shape_msgs
    PUBLIC
        ${CMAKE_BINARY_DIR}/generated/
        $<BUILD_INTERFACE:${GENERATED_INCLUDE_DIRS}>
        $<INSTALL_INTERFACE:include>)

target_link_libraries(shape_msgs
    PUBLIC CycloneDDS::ddsc CycloneDDS-CXX::ddscxx Boost::boost
    geometry_msgs
    )

target_compile_definitions(shape_msgs
    PUBLIC DDSCXX_NO_STD_OPTIONAL)

# Library depends on final sources being ready
add_dependencies(shape_msgs final_sources_shape_msgs)

# ------------------------------------------------------------
# Install (headers only, preserve layout)
# ------------------------------------------------------------
install(TARGETS shape_msgs
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib
        RUNTIME DESTINATION bin)

install(DIRECTORY ${CMAKE_BINARY_DIR}/generated/
        DESTINATION include
        FILES_MATCHING PATTERN "*.hpp"
        )

install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/
        DESTINATION include/${PROJECT_NAME}
        FILES_MATCHING PATTERN "*.idl"
)


# make <pkg> root dirs visible to consumers
file(GLOB CHILD_PKG_DIRS LIST_DIRECTORIES TRUE
     "${CMAKE_BINARY_DIR}/generated/*")
foreach(PKG_DIR IN LISTS CHILD_PKG_DIRS)
    target_include_directories(shape_msgs PUBLIC "${PKG_DIR}")
endforeach()