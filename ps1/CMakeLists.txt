cmake_minimum_required(VERSION 3.21)

project(funkin_ps1_probe LANGUAGES C CXX ASM VERSION 0.1.0)

psn00bsdk_add_executable(funkin-ps1-probe GPREL main.c)

psn00bsdk_add_cd_image(
	ps1-disc
	funkin-ps1-probe
	iso.xml
	DEPENDS funkin-ps1-probe system.cnf
)

# Optional CD-audio clock probe. This uses a generated, rights-safe click track
# while official stems remain local-only until their distribution terms and
# input files are available.
if(DEFINED FUNKIN_PS1_AUDIO_WAV AND EXISTS "${FUNKIN_PS1_AUDIO_WAV}")
	configure_file("${FUNKIN_PS1_AUDIO_WAV}" "${CMAKE_CURRENT_BINARY_DIR}/audio-probe.wav" COPYONLY)
	psn00bsdk_add_executable(funkin-ps1-audio-probe GPREL audio_probe.c)
	psn00bsdk_add_cd_image(
		ps1-audio-disc
		funkin-ps1-audio-probe
		audio_iso.xml
		DEPENDS funkin-ps1-audio-probe system.cnf "${CMAKE_CURRENT_BINARY_DIR}/audio-probe.wav"
	)
elseif(DEFINED FUNKIN_PS1_AUDIO_WAV)
	message(FATAL_ERROR "FUNKIN_PS1_AUDIO_WAV does not name an existing PCM WAV file")
endif()

# Optional PSn00bSDK CD-to-SPU ADPCM streaming probe. The SDK's reusable
# streaming implementation remains in the external SDK installation.
if(DEFINED FUNKIN_PS1_AUDIO_VAGI AND EXISTS "${FUNKIN_PS1_AUDIO_VAGI}")
	get_filename_component(_psn00bsdk_lib_dir "$ENV{PSN00BSDK_LIBS}" DIRECTORY)
	get_filename_component(_psn00bsdk_root "${_psn00bsdk_lib_dir}" DIRECTORY)
	set(_psn00bsdk_cdstream_dir
		"${_psn00bsdk_root}/share/psn00bsdk/examples/sound/cdstream")
	if(NOT EXISTS "${_psn00bsdk_cdstream_dir}/stream.c" OR
	   NOT EXISTS "${_psn00bsdk_cdstream_dir}/stream.h")
		message(FATAL_ERROR
			"PSn00bSDK cdstream example sources were not found under ${_psn00bsdk_cdstream_dir}")
	endif()
	configure_file("${FUNKIN_PS1_AUDIO_VAGI}"
		"${CMAKE_CURRENT_BINARY_DIR}/stream.vag" COPYONLY)
	psn00bsdk_add_executable(funkin-ps1-spu-probe GPREL
		spu_probe.c
		"${_psn00bsdk_cdstream_dir}/stream.c")
	target_compile_definitions(funkin-ps1-spu-probe PRIVATE TEST_CHANNELS=2)
	target_include_directories(funkin-ps1-spu-probe PRIVATE
		"${_psn00bsdk_cdstream_dir}")
	psn00bsdk_add_cd_image(
		ps1-spu-disc
		funkin-ps1-spu-probe
		spu_iso.xml
		DEPENDS funkin-ps1-spu-probe system.cnf
			"${CMAKE_CURRENT_BINARY_DIR}/stream.vag"
	)
elseif(DEFINED FUNKIN_PS1_AUDIO_VAGI)
	message(FATAL_ERROR "FUNKIN_PS1_AUDIO_VAGI does not name an existing VAGi file")
endif()

# Separate four-channel instrumental L/R + voice L/R stream probe. Keeping this
# as a distinct image preserves the stereo baseline and its fixture workflow.
if(DEFINED FUNKIN_PS1_AUDIO_VAGI_4CH AND EXISTS "${FUNKIN_PS1_AUDIO_VAGI_4CH}")
	get_filename_component(_psn00bsdk_lib_dir "$ENV{PSN00BSDK_LIBS}" DIRECTORY)
	get_filename_component(_psn00bsdk_root "${_psn00bsdk_lib_dir}" DIRECTORY)
	set(_psn00bsdk_cdstream_dir
		"${_psn00bsdk_root}/share/psn00bsdk/examples/sound/cdstream")
	if(NOT EXISTS "${_psn00bsdk_cdstream_dir}/stream.c" OR
	   NOT EXISTS "${_psn00bsdk_cdstream_dir}/stream.h")
		message(FATAL_ERROR
			"PSn00bSDK cdstream example sources were not found under ${_psn00bsdk_cdstream_dir}")
	endif()
	configure_file("${FUNKIN_PS1_AUDIO_VAGI_4CH}"
		"${CMAKE_CURRENT_BINARY_DIR}/stream-4ch.vag" COPYONLY)
	psn00bsdk_add_executable(funkin-ps1-spu-4ch-probe GPREL
		spu_probe.c
		"${_psn00bsdk_cdstream_dir}/stream.c")
	target_compile_definitions(funkin-ps1-spu-4ch-probe PRIVATE TEST_CHANNELS=4)
	target_include_directories(funkin-ps1-spu-4ch-probe PRIVATE
		"${_psn00bsdk_cdstream_dir}")
	psn00bsdk_add_cd_image(
		ps1-spu-4ch-disc
		funkin-ps1-spu-4ch-probe
		spu_4ch_iso.xml
		DEPENDS funkin-ps1-spu-4ch-probe system.cnf
			"${CMAKE_CURRENT_BINARY_DIR}/stream-4ch.vag"
	)
elseif(DEFINED FUNKIN_PS1_AUDIO_VAGI_4CH)
	message(FATAL_ERROR "FUNKIN_PS1_AUDIO_VAGI_4CH does not name an existing VAGi file")
endif()

# Full-length classic Bopeebo playback check. Its source OGGs are decoded and
# encoded to a six-channel VAGi outside the repository; no game assets are
# copied into Git. Circle mutes BF's player-voice pair while Dad remains live.
if(DEFINED FUNKIN_PS1_AUDIO_VAGI_BOPEEBO AND EXISTS "${FUNKIN_PS1_AUDIO_VAGI_BOPEEBO}")
	set(FUNKIN_PS1_AUDIO_SAMPLE_COUNT "1799280u" CACHE STRING
		"Source sample count used to stop the full-song Bopeebo probe")
	get_filename_component(_psn00bsdk_lib_dir "$ENV{PSN00BSDK_LIBS}" DIRECTORY)
	get_filename_component(_psn00bsdk_root "${_psn00bsdk_lib_dir}" DIRECTORY)
	set(_psn00bsdk_cdstream_dir
		"${_psn00bsdk_root}/share/psn00bsdk/examples/sound/cdstream")
	if(NOT EXISTS "${_psn00bsdk_cdstream_dir}/stream.c" OR
	   NOT EXISTS "${_psn00bsdk_cdstream_dir}/stream.h")
		message(FATAL_ERROR
			"PSn00bSDK cdstream example sources were not found under ${_psn00bsdk_cdstream_dir}")
	endif()
	configure_file("${FUNKIN_PS1_AUDIO_VAGI_BOPEEBO}"
		"${CMAKE_CURRENT_BINARY_DIR}/bopeebo.vag" COPYONLY)
	psn00bsdk_add_executable(funkin-ps1-bopeebo-audio GPREL
		spu_probe.c
		"${_psn00bsdk_cdstream_dir}/stream.c")
	target_compile_definitions(funkin-ps1-bopeebo-audio PRIVATE
		TEST_CHANNELS=6
		TEST_NO_LOOP=1
		TEST_TOTAL_SAMPLES=${FUNKIN_PS1_AUDIO_SAMPLE_COUNT})
	target_include_directories(funkin-ps1-bopeebo-audio PRIVATE
		"${_psn00bsdk_cdstream_dir}")
	psn00bsdk_add_cd_image(
		ps1-bopeebo-audio-disc
		funkin-ps1-bopeebo-audio
		bopeebo_audio_iso.xml
		DEPENDS funkin-ps1-bopeebo-audio system.cnf
			"${CMAKE_CURRENT_BINARY_DIR}/bopeebo.vag"
	)
elseif(DEFINED FUNKIN_PS1_AUDIO_VAGI_BOPEEBO)
	message(FATAL_ERROR "FUNKIN_PS1_AUDIO_VAGI_BOPEEBO does not name an existing VAGi file")
endif()

# Comparative four-channel Bopeebo image. The voice stems are downmixed once
# during encoding; SPU channel volumes provide runtime panning without re-encode.
if(DEFINED FUNKIN_PS1_AUDIO_VAGI_BOPEEBO_4CH AND EXISTS "${FUNKIN_PS1_AUDIO_VAGI_BOPEEBO_4CH}")
	set(FUNKIN_PS1_AUDIO_4CH_SAMPLE_COUNT "3509453u" CACHE STRING
		"Source sample count used to stop the four-channel Bopeebo probe")
	get_filename_component(_psn00bsdk_lib_dir "$ENV{PSN00BSDK_LIBS}" DIRECTORY)
	get_filename_component(_psn00bsdk_root "${_psn00bsdk_lib_dir}" DIRECTORY)
	set(_psn00bsdk_cdstream_dir
		"${_psn00bsdk_root}/share/psn00bsdk/examples/sound/cdstream")
	if(NOT EXISTS "${_psn00bsdk_cdstream_dir}/stream.c" OR
	   NOT EXISTS "${_psn00bsdk_cdstream_dir}/stream.h")
		message(FATAL_ERROR
			"PSn00bSDK cdstream example sources were not found under ${_psn00bsdk_cdstream_dir}")
	endif()
	find_package(Python3 REQUIRED COMPONENTS Interpreter)
	set(_bopeebo_sfx_header "${CMAKE_CURRENT_BINARY_DIR}/bopeebo_sfx_data.h")
	set(_bopeebo_sfx_vag "${CMAKE_CURRENT_BINARY_DIR}/bopeebo_sfx.vag")
	add_custom_command(
		OUTPUT "${_bopeebo_sfx_header}" "${_bopeebo_sfx_vag}"
		COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/generate_ps1_sfx.py"
			--header "${_bopeebo_sfx_header}" --vag "${_bopeebo_sfx_vag}"
		DEPENDS generate_ps1_sfx.py convert_bopeebo_to_vagi.py
		VERBATIM
	)
	configure_file("${FUNKIN_PS1_AUDIO_VAGI_BOPEEBO_4CH}"
		"${CMAKE_CURRENT_BINARY_DIR}/stream-4ch.vag" COPYONLY)
	psn00bsdk_add_executable(funkin-ps1-bopeebo-4ch-audio GPREL
		spu_probe.c
		"${_psn00bsdk_cdstream_dir}/stream.c"
		"${_bopeebo_sfx_header}")
	add_custom_target(funkin-ps1-bopeebo-sfx DEPENDS "${_bopeebo_sfx_header}" "${_bopeebo_sfx_vag}")
	add_dependencies(funkin-ps1-bopeebo-4ch-audio funkin-ps1-bopeebo-sfx)
	target_compile_definitions(funkin-ps1-bopeebo-4ch-audio PRIVATE
		TEST_CHANNELS=4
		TEST_BOPEEBO_4CH=1
		TEST_NO_LOOP=1
		TEST_TOTAL_SAMPLES=${FUNKIN_PS1_AUDIO_4CH_SAMPLE_COUNT})
	target_include_directories(funkin-ps1-bopeebo-4ch-audio PRIVATE
		"${_psn00bsdk_cdstream_dir}" "${CMAKE_CURRENT_BINARY_DIR}")
	psn00bsdk_add_cd_image(
		ps1-bopeebo-audio-4ch-disc
		funkin-ps1-bopeebo-4ch-audio
		bopeebo_audio_4ch_iso.xml
		DEPENDS funkin-ps1-bopeebo-4ch-audio system.cnf
			"${CMAKE_CURRENT_BINARY_DIR}/stream-4ch.vag"
			"${_bopeebo_sfx_vag}"
	)
elseif(DEFINED FUNKIN_PS1_AUDIO_VAGI_BOPEEBO_4CH)
	message(FATAL_ERROR "FUNKIN_PS1_AUDIO_VAGI_BOPEEBO_4CH does not name an existing VAGi file")
endif()

# First playable Bopeebo Normal slice. The official chart JSON is supplied from
# the pinned assets checkout or local work folder and converted into a small
# generated C table; neither chart data nor official audio is vendored here.
if(DEFINED FUNKIN_PS1_BOPEEBO_CHART_JSON AND EXISTS "${FUNKIN_PS1_BOPEEBO_CHART_JSON}" AND
	DEFINED FUNKIN_PS1_AUDIO_VAGI_BOPEEBO_4CH AND EXISTS "${FUNKIN_PS1_AUDIO_VAGI_BOPEEBO_4CH}")
	option(FUNKIN_PS1_DAD_LANES_DEFAULT "Show Dad's autoplay lanes when Bopeebo starts" ON)
	option(FUNKIN_PS1_DIAGNOSTICS_DEFAULT "Show the PS1 diagnostics overlay at startup" OFF)
	option(FUNKIN_PS1_SCENE_DEMO_DEFAULT "Build a camera-only scene demo without gameplay penalties" OFF)
	get_filename_component(_psn00bsdk_lib_dir "$ENV{PSN00BSDK_LIBS}" DIRECTORY)
	get_filename_component(_psn00bsdk_root "${_psn00bsdk_lib_dir}" DIRECTORY)
	set(_psn00bsdk_cdstream_dir
		"${_psn00bsdk_root}/share/psn00bsdk/examples/sound/cdstream")
	if(NOT EXISTS "${_psn00bsdk_cdstream_dir}/stream.c" OR
	   NOT EXISTS "${_psn00bsdk_cdstream_dir}/stream.h")
		message(FATAL_ERROR "PSn00bSDK cdstream example sources were not found under ${_psn00bsdk_cdstream_dir}")
	endif()
	find_package(Python3 REQUIRED COMPONENTS Interpreter)
	set(_playable_chart_header "${CMAKE_CURRENT_BINARY_DIR}/bopeebo_chart.h")
	set(FUNKIN_PS1_ASSETS_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../assets" CACHE PATH
		"Root of the pinned Funkin.assets submodule")
	if(NOT EXISTS "${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/BOYFRIEND.xml")
		message(FATAL_ERROR "FUNKIN_PS1_ASSETS_DIR does not contain the pinned official asset checkout")
	endif()
	if(NOT FUNKIN_PS1_FFMPEG OR NOT EXISTS "${FUNKIN_PS1_FFMPEG}")
		find_program(FUNKIN_PS1_FFMPEG NAMES ffmpeg)
	endif()
	if(NOT FUNKIN_PS1_FFMPEG OR NOT EXISTS "${FUNKIN_PS1_FFMPEG}")
		message(FATAL_ERROR "Set FUNKIN_PS1_FFMPEG to an ffmpeg executable for deterministic art conversion")
	endif()
	set(_playable_visual_header "${CMAKE_CURRENT_BINARY_DIR}/bopeebo_visual_data.h")
	set(_visual_asset_dependencies
		"${FUNKIN_PS1_ASSETS_DIR}/preload/data/stages/mainStage.json"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/stageback.png"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/stagefront.png"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/stagecurtains.png"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/BOYFRIEND.png"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/BOYFRIEND.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/notes.png"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/notes.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/noteStrumline.png"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/noteStrumline.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/NOTE_hold_assets.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/icons/icon-dad.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/icons/icon-bf.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/ui/popup/funkin/sick.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/ui/popup/funkin/good.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/ui/popup/funkin/bad.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/ui/popup/funkin/shit.png")
	add_custom_command(
		OUTPUT "${_playable_visual_header}"
		COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/convert_bopeebo_visuals.py"
			--assets "${FUNKIN_PS1_ASSETS_DIR}"
			--ffmpeg "${FUNKIN_PS1_FFMPEG}"
			--output "${_playable_visual_header}"
		DEPENDS convert_bopeebo_visuals.py animate_preview.py ${_visual_asset_dependencies}
		VERBATIM
	)
	add_custom_command(
		OUTPUT "${_playable_chart_header}"
		COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/convert_bopeebo_chart.py"
			"${FUNKIN_PS1_BOPEEBO_CHART_JSON}" "${_playable_chart_header}" --rate 43008
		DEPENDS convert_bopeebo_chart.py "${FUNKIN_PS1_BOPEEBO_CHART_JSON}"
		VERBATIM
	)
	configure_file("${FUNKIN_PS1_AUDIO_VAGI_BOPEEBO_4CH}"
		"${CMAKE_CURRENT_BINARY_DIR}/stream-playable.vag" COPYONLY)
	psn00bsdk_add_executable(funkin-ps1-bopeebo-playable GPREL
		spu_probe.c "${_psn00bsdk_cdstream_dir}/stream.c"
		"${_playable_chart_header}" "${_playable_visual_header}" "${_bopeebo_sfx_header}")
	add_dependencies(funkin-ps1-bopeebo-playable funkin-ps1-bopeebo-sfx)
	target_compile_definitions(funkin-ps1-bopeebo-playable PRIVATE
		TEST_CHANNELS=4 TEST_BOPEEBO_4CH=1 TEST_PLAYABLE_BOPEEBO=1
		GAME_DAD_LANES_DEFAULT=$<BOOL:${FUNKIN_PS1_DAD_LANES_DEFAULT}>
		GAME_DIAGNOSTICS_DEFAULT=$<BOOL:${FUNKIN_PS1_DIAGNOSTICS_DEFAULT}>
		GAME_SCENE_DEMO_DEFAULT=$<BOOL:${FUNKIN_PS1_SCENE_DEMO_DEFAULT}>
		TEST_NO_LOOP=1 TEST_TOTAL_SAMPLES=3509453u)
	target_include_directories(funkin-ps1-bopeebo-playable PRIVATE
		"${_psn00bsdk_cdstream_dir}" "${CMAKE_CURRENT_BINARY_DIR}")
	psn00bsdk_add_cd_image(
		ps1-bopeebo-playable-disc funkin-ps1-bopeebo-playable
		bopeebo_playable_iso.xml
		DEPENDS funkin-ps1-bopeebo-playable system.cnf
			"${CMAKE_CURRENT_BINARY_DIR}/stream-playable.vag"
			"${_bopeebo_sfx_vag}")
elseif(DEFINED FUNKIN_PS1_BOPEEBO_CHART_JSON OR DEFINED FUNKIN_PS1_AUDIO_VAGI_BOPEEBO_4CH)
	message(FATAL_ERROR "Playable Bopeebo requires both FUNKIN_PS1_BOPEEBO_CHART_JSON and FUNKIN_PS1_AUDIO_VAGI_BOPEEBO_4CH to name existing files")
endif()
