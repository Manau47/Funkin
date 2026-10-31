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
	option(FUNKIN_PS1_ARROW_DIAGNOSTIC_DEFAULT "Autostart Bopeebo with the four-direction arrow QA sheet" OFF)
	option(FUNKIN_PS1_JUDGEMENT_TEST_DEFAULT "Autostart a no-controller four-judgement gameplay QA run" OFF)
	option(FUNKIN_PS1_JUDGEMENT_VISUAL_TEST_DEFAULT "Build a no-audio isolated four-judgement visual test" OFF)
	option(FUNKIN_PS1_JUDGEMENT_SOLID_PROBE_DEFAULT "Replace judgement art with a same-bounds solid GPU primitive for diagnosis" OFF)
	option(FUNKIN_PS1_JUDGEMENT_TEXTURE_PROBE_DEFAULT "Use a known BF miss frame through the judgement FT4 path for diagnosis" OFF)
	option(FUNKIN_PS1_JUDGEMENT_CLUT_PROBE_DEFAULT "Draw judgement texels with the known-working BF CLUT for diagnosis" OFF)
	option(FUNKIN_PS1_JUDGEMENT_POPUP_CLUT_PROBE_DEFAULT "Draw known BF texels with the popup CLUT for diagnosis" OFF)
	option(FUNKIN_PS1_JUDGEMENT_POPUP_CLUT_RELOCATE_PROBE_DEFAULT "Load popup palette at known-working BF CLUT address for diagnosis" OFF)
	option(FUNKIN_PS1_JUDGEMENT_POPUP_CLUT_SLOT_PROBE_DEFAULT "Test popup palette in a free neighboring CLUT slot" OFF)
	option(FUNKIN_PS1_SCENE_DEMO_DEFAULT "Build a camera-only scene demo without gameplay penalties" OFF)
	option(FUNKIN_PS1_HEALTH_BAR_TEST_DEFAULT "Build a visual-only health bar calibration disc" OFF)
	option(FUNKIN_PS1_STARTUP_MAIN_MARKER "Stop the playable executable at main entry and display a fixed white GPU frame" OFF)
	option(FUNKIN_PS1_STARTUP_AFTER_BSS_MARKER "Replace the PSn00bSDK startup entry and stop after the real executable BSS clear" OFF)
	option(FUNKIN_PS1_STARTUP_BEFORE_BSS_MARKER "Replace the PSn00bSDK startup entry and stop before clearing executable BSS" OFF)
	get_filename_component(_psn00bsdk_lib_dir "$ENV{PSN00BSDK_LIBS}" DIRECTORY)
	get_filename_component(_psn00bsdk_root "${_psn00bsdk_lib_dir}" DIRECTORY)
	set(_psn00bsdk_cdstream_dir
		"${_psn00bsdk_root}/share/psn00bsdk/examples/sound/cdstream")
	if(NOT EXISTS "${_psn00bsdk_cdstream_dir}/stream.c" OR
	   NOT EXISTS "${_psn00bsdk_cdstream_dir}/stream.h")
		message(FATAL_ERROR "PSn00bSDK cdstream example sources were not found under ${_psn00bsdk_cdstream_dir}")
	endif()
	find_package(Python3 REQUIRED COMPONENTS Interpreter)
	set(_playable_chart_header "${CMAKE_CURRENT_BINARY_DIR}/week1_catalog.h")
	set(_song_audio_dir "${CMAKE_CURRENT_BINARY_DIR}/catalog-audio")
	set(_song_audio_outputs
		"${_song_audio_dir}/fresh.vag"
		"${_song_audio_dir}/dadbattle.vag"
		"${_song_audio_dir}/tutorial.vag"
		"${_song_audio_dir}/spookeez.vag"
		"${_song_audio_dir}/south.vag"
		"${_song_audio_dir}/monster.vag"
		"${_song_audio_dir}/pico.vag"
		"${_song_audio_dir}/philly-nice.vag"
		"${_song_audio_dir}/blammed.vag")
	set(_song_chart_dir "${_song_audio_dir}/charts")
	set(_song_chart_outputs)
	foreach(_song tutorial bopeebo fresh dadbattle spookeez south monster pico philly-nice blammed)
		if(_song STREQUAL "tutorial")
			set(_chart_prefix TUT)
		elseif(_song STREQUAL "bopeebo")
			set(_chart_prefix BOP)
		elseif(_song STREQUAL "fresh")
			set(_chart_prefix FRE)
		elseif(_song STREQUAL "dadbattle")
			set(_chart_prefix DAD)
		elseif(_song STREQUAL "spookeez")
			set(_chart_prefix SPO)
		elseif(_song STREQUAL "south")
			set(_chart_prefix SOU)
		elseif(_song STREQUAL "monster")
			set(_chart_prefix MON)
		elseif(_song STREQUAL "pico")
			set(_chart_prefix PIC)
		elseif(_song STREQUAL "philly-nice")
			set(_chart_prefix PHI)
		else()
			set(_chart_prefix BLA)
		endif()
		foreach(_difficulty E N H)
			list(APPEND _song_chart_outputs "${_song_chart_dir}/${_chart_prefix}${_difficulty}.BIN")
		endforeach()
	endforeach()
	set(FUNKIN_PS1_ASSETS_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../assets" CACHE PATH
		"Root of the pinned Funkin.assets submodule")
	set(FUNKIN_PS1_OPTIONS_ART "${CMAKE_CURRENT_SOURCE_DIR}/../outputs/menu-options-concept-v2.png" CACHE FILEPATH
		"Approved local OPTIONS menu lettering PNG (kept outside Git)")
	set(FUNKIN_PS1_PRECONVERTED_BASE_DIR "" CACHE PATH
		"Optional directory with reusable converted Week 1-3/menu packages")
	set(FUNKIN_PS1_PRECONVERTED_WEEK4_DIR "" CACHE PATH
		"Optional directory with a reusable converted Week 4 package")
	set(FUNKIN_PS1_PRECONVERTED_WEEK5_DIR "" CACHE PATH
		"Optional directory with a reusable converted Week 5 package")
	set(FUNKIN_PS1_PRECONVERTED_WEEK6_DIR "" CACHE PATH
		"Optional directory with a reusable converted Week 6 package")
	set(FUNKIN_PS1_PRECONVERTED_WEEK7_DIR "" CACHE PATH
		"Optional directory with a reusable converted Week 7 package")
	set(FUNKIN_PS1_PRECONVERTED_WEEKEND1_DIR "" CACHE PATH
		"Optional directory with a reusable converted WeekEnd 1 package")
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
	set(_week2_visual_payload "${CMAKE_CURRENT_BINARY_DIR}/week2-scene.bin")
	set(_week1_visual_payload "${CMAKE_CURRENT_BINARY_DIR}/week1-scene.bin")
	set(_week3_visual_payload "${CMAKE_CURRENT_BINARY_DIR}/week3-scene.bin")
	set(_week4_visual_header "${CMAKE_CURRENT_BINARY_DIR}/week4_visual_data.h")
	set(_week4_visual_payload "${CMAKE_CURRENT_BINARY_DIR}/week4-scene.bin")
	set(_visual_asset_dependencies
		"${FUNKIN_PS1_ASSETS_DIR}/preload/data/stages/mainStage.json"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/stageback.png"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/stagefront.png"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/stagecurtains.png"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/BOYFRIEND.png"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/BOYFRIEND.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/data/characters/bf.json"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/data/characters/dad.json"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/data/characters/gf.json"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/dad/Animation.json"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/dad/spritemap1.json"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/dad/spritemap1.png"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/gf/Animation.json"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/gf/spritemap1.json"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/gf/spritemap1.png"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/bf-death/Animation.json"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/bf-death/spritemap1.json"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/bf-death/spritemap1.png"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/notes.png"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/notes.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/noteStrumline.png"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/noteStrumline.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/NOTE_hold_assets.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/icons/icon-dad.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/icons/icon-bf.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/icons/icon-gf.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/logoBumpin.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/logoBumpin.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/menuBG.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/freeplayBGweek1-bf.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/glowingText.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/freeplayeasy.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/freeplaynormal.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/freeplayhard.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/freeplaySelector.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/freeplaySelector.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/fonts/vcr-bold.ttf"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/freeplay-boyfriend/Animation.json"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/freeplay-boyfriend/spritemap1.json"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/freeplay-boyfriend/spritemap1.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/albumRoll/volume1.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/freeplayCapsule/capsule/freeplayCapsule.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/freeplayCapsule/capsule/freeplayCapsule.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/icons/gfpixel.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/icons/gfpixel.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/icons/dadpixel.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/icons/dadpixel.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/icons/spookypixel.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/icons/spookypixel.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/icons/picopixel.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/icons/picopixel.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/icons/mompixel.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/icons/mompixel.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/icons/monsterpixel.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/icons/monsterpixel.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/icons/parents-christmaspixel.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/icons/parents-christmaspixel.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/icons/senpaipixel.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/icons/senpaipixel.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/icons/spiritpixel.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/icons/spiritpixel.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/icons/tankmanpixel.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/icons/tankmanpixel.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/icons/darnellpixel.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/freeplay/icons/darnellpixel.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/mainmenu/freeplay.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/mainmenu/freeplay.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/mainmenu/storymode.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/mainmenu/storymode.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/mainmenu/merch.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/mainmenu/merch.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/mainmenu/options.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/mainmenu/options.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/mainmenu/credits.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/mainmenu/credits.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/music/freakyMenu/freakyMenu.ogg"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/sounds/scrollMenu.ogg"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/sounds/confirmMenu.ogg"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/sounds/cancelMenu.ogg"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/music/gameplay/gameover/gameOver.ogg"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/music/gameplay/gameover/gameOverEnd.ogg"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/sounds/gameplay/gameover/fnf_loss_sfx.ogg"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/sounds/missnote1.ogg"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/sounds/missnote2.ogg"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/sounds/missnote3.ogg"
		"${FUNKIN_PS1_ASSETS_DIR}/week2/sounds/thunder_1.ogg"
		"${FUNKIN_PS1_ASSETS_DIR}/week2/sounds/thunder_2.ogg"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/ui/popup/funkin/sick.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/ui/popup/funkin/good.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/ui/popup/funkin/bad.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/ui/popup/funkin/shit.png")
	list(APPEND _visual_asset_dependencies
		"${FUNKIN_PS1_ASSETS_DIR}/preload/data/stages/spookyMansion.json"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/data/characters/spooky.json"
		"${FUNKIN_PS1_ASSETS_DIR}/week2/images/halloween_bg/spritemap1.json"
		"${FUNKIN_PS1_ASSETS_DIR}/week2/images/halloween_bg/spritemap1.png"
		"${FUNKIN_PS1_ASSETS_DIR}/week2/images/halloween_bg/Animation.json"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/SpookyKids.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/SpookyKids.png"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/monster/Animation.json"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/monster/spritemap1.json"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/monster/spritemap1.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/data/characters/monster.json"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/icons/icon-spooky.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/icons/icon-monster.png")
	list(APPEND _visual_asset_dependencies
		"${FUNKIN_PS1_ASSETS_DIR}/preload/data/stages/phillyTrain.json"
		"${FUNKIN_PS1_ASSETS_DIR}/week3/images/philly/sky.png"
		"${FUNKIN_PS1_ASSETS_DIR}/week3/images/philly/city.png"
		"${FUNKIN_PS1_ASSETS_DIR}/week3/images/philly/win.png"
		"${FUNKIN_PS1_ASSETS_DIR}/week3/images/philly/behindTrain.png"
		"${FUNKIN_PS1_ASSETS_DIR}/week3/images/philly/street.png"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/pico/basic-animations/Animation.json"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/pico/basic-animations/spritemap1.json"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/pico/basic-animations/spritemap1.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/icons/icon-pico.png")
	if(EXISTS "${FUNKIN_PS1_OPTIONS_ART}")
		list(APPEND _visual_asset_dependencies "${FUNKIN_PS1_OPTIONS_ART}")
		set(_options_art_args --options-art "${FUNKIN_PS1_OPTIONS_ART}")
	else()
		message(STATUS "Approved OPTIONS PNG unavailable; using pinned official options.png for fallback build")
		set(_options_art_args)
	endif()
	if(FUNKIN_PS1_PRECONVERTED_BASE_DIR)
		foreach(_base_package_file
			bopeebo_visual_data.h week1-scene.bin week2-scene.bin week3-scene.bin)
			if(NOT EXISTS "${FUNKIN_PS1_PRECONVERTED_BASE_DIR}/${_base_package_file}")
				message(FATAL_ERROR "Missing reusable base package file: ${FUNKIN_PS1_PRECONVERTED_BASE_DIR}/${_base_package_file}")
			endif()
			configure_file("${FUNKIN_PS1_PRECONVERTED_BASE_DIR}/${_base_package_file}"
				"${CMAKE_CURRENT_BINARY_DIR}/${_base_package_file}" COPYONLY)
		endforeach()
	else()
		add_custom_command(
			OUTPUT "${_playable_visual_header}" "${_week2_visual_payload}" "${_week1_visual_payload}" "${_week3_visual_payload}"
			COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/convert_bopeebo_visuals.py"
				--assets "${FUNKIN_PS1_ASSETS_DIR}"
				--ffmpeg "${FUNKIN_PS1_FFMPEG}"
				${_options_art_args}
				--week2-pages-output "${_week2_visual_payload}"
				--week1-pages-output "${_week1_visual_payload}"
				--week3-pages-output "${_week3_visual_payload}"
				--output "${_playable_visual_header}"
			DEPENDS convert_bopeebo_visuals.py animate_preview.py ${_visual_asset_dependencies}
			VERBATIM
		)
	endif()
	set(_song_catalog_dependencies
		"${CMAKE_CURRENT_SOURCE_DIR}/generate_ps1_song_catalog.py"
		"${CMAKE_CURRENT_SOURCE_DIR}/convert_bopeebo_to_vagi.py")
	foreach(_song tutorial bopeebo fresh dadbattle spookeez south monster pico philly-nice blammed)
		list(APPEND _song_catalog_dependencies
			"${FUNKIN_PS1_ASSETS_DIR}/preload/data/songs/${_song}/${_song}-chart.json"
			"${FUNKIN_PS1_ASSETS_DIR}/preload/data/songs/${_song}/${_song}-metadata.json"
			"${FUNKIN_PS1_ASSETS_DIR}/songs/${_song}/Inst.ogg"
			"${FUNKIN_PS1_ASSETS_DIR}/songs/${_song}/Voices-bf.ogg")
		if(_song STREQUAL "tutorial")
			list(APPEND _song_catalog_dependencies "${FUNKIN_PS1_ASSETS_DIR}/songs/${_song}/Voices-gf.ogg")
		elseif(_song STREQUAL "spookeez" OR _song STREQUAL "south")
			list(APPEND _song_catalog_dependencies "${FUNKIN_PS1_ASSETS_DIR}/songs/${_song}/Voices-spooky.ogg")
		elseif(_song STREQUAL "monster")
			list(APPEND _song_catalog_dependencies "${FUNKIN_PS1_ASSETS_DIR}/songs/${_song}/Voices-monster.ogg")
		elseif(_song STREQUAL "pico" OR _song STREQUAL "philly-nice" OR _song STREQUAL "blammed")
			list(APPEND _song_catalog_dependencies "${FUNKIN_PS1_ASSETS_DIR}/songs/${_song}/Voices-pico.ogg")
		else()
			list(APPEND _song_catalog_dependencies "${FUNKIN_PS1_ASSETS_DIR}/songs/${_song}/Voices-dad.ogg")
		endif()
	endforeach()
	if(FUNKIN_PS1_PRECONVERTED_BASE_DIR)
		set(_base_song_files week1_catalog.h)
		foreach(_song_audio fresh dadbattle tutorial spookeez south monster pico philly-nice blammed)
			list(APPEND _base_song_files "catalog-audio/${_song_audio}.vag")
		endforeach()
		list(APPEND _base_song_files
			catalog-audio/charts/TUTE.BIN catalog-audio/charts/TUTN.BIN catalog-audio/charts/TUTH.BIN
			catalog-audio/charts/BOPE.BIN catalog-audio/charts/BOPN.BIN catalog-audio/charts/BOPH.BIN
			catalog-audio/charts/FREE.BIN catalog-audio/charts/FREN.BIN catalog-audio/charts/FREH.BIN
			catalog-audio/charts/DADE.BIN catalog-audio/charts/DADN.BIN catalog-audio/charts/DADH.BIN
			catalog-audio/charts/SPOE.BIN catalog-audio/charts/SPON.BIN catalog-audio/charts/SPOH.BIN
			catalog-audio/charts/SOUE.BIN catalog-audio/charts/SOUN.BIN catalog-audio/charts/SOUH.BIN
			catalog-audio/charts/MONE.BIN catalog-audio/charts/MONN.BIN catalog-audio/charts/MONH.BIN
			catalog-audio/charts/PICE.BIN catalog-audio/charts/PICN.BIN catalog-audio/charts/PICH.BIN
			catalog-audio/charts/PHIE.BIN catalog-audio/charts/PHIN.BIN catalog-audio/charts/PHIH.BIN
			catalog-audio/charts/BLAE.BIN catalog-audio/charts/BLAN.BIN catalog-audio/charts/BLAH.BIN)
		foreach(_base_package_file IN LISTS _base_song_files)
			if(NOT EXISTS "${FUNKIN_PS1_PRECONVERTED_BASE_DIR}/${_base_package_file}")
				message(FATAL_ERROR "Missing reusable base package file: ${FUNKIN_PS1_PRECONVERTED_BASE_DIR}/${_base_package_file}")
			endif()
			get_filename_component(_base_destination_dir "${CMAKE_CURRENT_BINARY_DIR}/${_base_package_file}" DIRECTORY)
			file(MAKE_DIRECTORY "${_base_destination_dir}")
			configure_file("${FUNKIN_PS1_PRECONVERTED_BASE_DIR}/${_base_package_file}"
				"${CMAKE_CURRENT_BINARY_DIR}/${_base_package_file}" COPYONLY)
		endforeach()
	else()
		add_custom_command(
			OUTPUT "${_playable_chart_header}" ${_song_audio_outputs} ${_song_chart_outputs}
			COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/generate_ps1_song_catalog.py"
				--assets "${FUNKIN_PS1_ASSETS_DIR}"
				--ffmpeg "${FUNKIN_PS1_FFMPEG}"
				--output-dir "${_song_audio_dir}"
				--header "${_playable_chart_header}" --chart-dir "${_song_chart_dir}" --rate 43008
			DEPENDS ${_song_catalog_dependencies}
			VERBATIM
		)
	endif()
	# Week 4 gets a separate incremental generator. It reuses the generated
	# Week 1-3 catalog and does not decode or rewrite those existing assets.
	set(_week4_audio_dir "${CMAKE_CURRENT_BINARY_DIR}/week4-audio")
	set(_week4_chart_dir "${_week4_audio_dir}/charts")
	set(_week4_header "${CMAKE_CURRENT_BINARY_DIR}/week4_catalog.h")
	set(_week4_audio_outputs
		"${_week4_audio_dir}/satin.vag"
		"${_week4_audio_dir}/high.vag"
		"${_week4_audio_dir}/milf.vag")
	set(_week4_chart_outputs)
	foreach(_song satin-panties high milf)
		if(_song STREQUAL "satin-panties")
			set(_week4_chart_prefix SAT)
		elseif(_song STREQUAL "high")
			set(_week4_chart_prefix HIG)
		else()
			set(_week4_chart_prefix MIL)
		endif()
		foreach(_difficulty E N H)
			list(APPEND _week4_chart_outputs "${_week4_chart_dir}/${_week4_chart_prefix}${_difficulty}.BIN")
		endforeach()
	endforeach()
	set(_week4_dependencies
		"${CMAKE_CURRENT_SOURCE_DIR}/generate_ps1_week4_assets.py"
		"${CMAKE_CURRENT_SOURCE_DIR}/generate_ps1_song_catalog.py"
		"${CMAKE_CURRENT_SOURCE_DIR}/convert_bopeebo_to_vagi.py"
		"${CMAKE_CURRENT_SOURCE_DIR}/convert_bopeebo_visuals.py"
		"${CMAKE_CURRENT_SOURCE_DIR}/animate_preview.py"
		"${_playable_chart_header}")
	foreach(_song satin-panties high milf)
		list(APPEND _week4_dependencies
			"${FUNKIN_PS1_ASSETS_DIR}/preload/data/songs/${_song}/${_song}-chart.json"
			"${FUNKIN_PS1_ASSETS_DIR}/preload/data/songs/${_song}/${_song}-metadata.json"
			"${FUNKIN_PS1_ASSETS_DIR}/songs/${_song}/Inst.ogg"
			"${FUNKIN_PS1_ASSETS_DIR}/songs/${_song}/Voices-bf.ogg"
			"${FUNKIN_PS1_ASSETS_DIR}/songs/${_song}/Voices-mom.ogg")
	endforeach()
	list(APPEND _week4_dependencies
		"${FUNKIN_PS1_ASSETS_DIR}/preload/data/stages/limoRide.json"
		"${FUNKIN_PS1_ASSETS_DIR}/week4/images/limo/limoSunset.png"
		"${FUNKIN_PS1_ASSETS_DIR}/week4/images/limo/bgLimo.png"
		"${FUNKIN_PS1_ASSETS_DIR}/week4/images/limo/bgLimo.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/week4/images/limo/limoDrive.png"
		"${FUNKIN_PS1_ASSETS_DIR}/week4/images/limo/limoDrive.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/momCar/Animation.json"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/momCar/spritemap1.json"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/momCar/spritemap1.png"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/gfCar/Animation.json"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/gfCar/spritemap1.json"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/gfCar/spritemap1.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/icons/icon-mom.png")
	if(FUNKIN_PS1_PRECONVERTED_WEEK4_DIR)
		set(_week4_package_files
			week4_catalog.h week4_visual_data.h week4-scene.bin
			week4-audio/satin.vag week4-audio/high.vag week4-audio/milf.vag
			week4-audio/charts/SATE.BIN week4-audio/charts/SATN.BIN week4-audio/charts/SATH.BIN
			week4-audio/charts/HIGE.BIN week4-audio/charts/HIGN.BIN week4-audio/charts/HIGH.BIN
			week4-audio/charts/MILE.BIN week4-audio/charts/MILN.BIN week4-audio/charts/MILH.BIN)
		foreach(_week4_package_file IN LISTS _week4_package_files)
			if(NOT EXISTS "${FUNKIN_PS1_PRECONVERTED_WEEK4_DIR}/${_week4_package_file}")
				message(FATAL_ERROR "Missing reusable Week 4 package file: ${FUNKIN_PS1_PRECONVERTED_WEEK4_DIR}/${_week4_package_file}")
			endif()
			get_filename_component(_week4_destination_dir "${CMAKE_CURRENT_BINARY_DIR}/${_week4_package_file}" DIRECTORY)
			file(MAKE_DIRECTORY "${_week4_destination_dir}")
			configure_file("${FUNKIN_PS1_PRECONVERTED_WEEK4_DIR}/${_week4_package_file}"
				"${CMAKE_CURRENT_BINARY_DIR}/${_week4_package_file}" COPYONLY)
		endforeach()
	else()
		add_custom_command(
			OUTPUT "${_week4_header}" ${_week4_audio_outputs} ${_week4_chart_outputs}
				"${_week4_visual_header}" "${_week4_visual_payload}"
			COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/generate_ps1_week4_assets.py"
				--assets "${FUNKIN_PS1_ASSETS_DIR}"
				--ffmpeg "${FUNKIN_PS1_FFMPEG}"
				--output-dir "${_week4_audio_dir}"
				--header "${_week4_header}"
				--chart-dir "${_week4_chart_dir}"
				--scene "${_week4_visual_payload}"
				--visual-header "${_week4_visual_header}"
			DEPENDS ${_week4_dependencies}
			VERBATIM
		)
	endif()
	# Week 5 classic content is generated/loaded independently from Weeks 1-4.
	set(_week5_audio_dir "${CMAKE_CURRENT_BINARY_DIR}/week5-audio")
	set(_week5_chart_dir "${_week5_audio_dir}/charts")
	set(_week5_header "${CMAKE_CURRENT_BINARY_DIR}/week5_catalog.h")
	set(_week5_visual_header "${CMAKE_CURRENT_BINARY_DIR}/week5_visual_data.h")
	set(_week5_scene "${CMAKE_CURRENT_BINARY_DIR}/week5-scene.bin")
	set(_week5_audio_outputs
		"${_week5_audio_dir}/cocoa.vag"
		"${_week5_audio_dir}/eggnog.vag"
		"${_week5_audio_dir}/winter.vag")
	set(_week5_chart_outputs)
	foreach(_song_code COC EGG WIN)
		foreach(_difficulty E N H)
			list(APPEND _week5_chart_outputs "${_week5_chart_dir}/${_song_code}${_difficulty}.BIN")
		endforeach()
	endforeach()
	if(FUNKIN_PS1_PRECONVERTED_WEEK5_DIR)
		set(_week5_package_files
			week5_catalog.h week5_visual_data.h week5-scene.bin
			week5-audio/cocoa.vag week5-audio/eggnog.vag week5-audio/winter.vag
			week5-audio/charts/COCE.BIN week5-audio/charts/COCN.BIN week5-audio/charts/COCH.BIN
			week5-audio/charts/EGGE.BIN week5-audio/charts/EGGN.BIN week5-audio/charts/EGGH.BIN
			week5-audio/charts/WINE.BIN week5-audio/charts/WINN.BIN week5-audio/charts/WINH.BIN)
		foreach(_week5_package_file IN LISTS _week5_package_files)
			if(NOT EXISTS "${FUNKIN_PS1_PRECONVERTED_WEEK5_DIR}/${_week5_package_file}")
				message(FATAL_ERROR "Missing reusable Week 5 package file: ${FUNKIN_PS1_PRECONVERTED_WEEK5_DIR}/${_week5_package_file}")
			endif()
			get_filename_component(_week5_destination_dir "${CMAKE_CURRENT_BINARY_DIR}/${_week5_package_file}" DIRECTORY)
			file(MAKE_DIRECTORY "${_week5_destination_dir}")
			configure_file("${FUNKIN_PS1_PRECONVERTED_WEEK5_DIR}/${_week5_package_file}"
				"${CMAKE_CURRENT_BINARY_DIR}/${_week5_package_file}" COPYONLY)
		endforeach()
	else()
		set(_week5_dependencies
			"${CMAKE_CURRENT_SOURCE_DIR}/generate_ps1_week5_assets.py"
			"${CMAKE_CURRENT_SOURCE_DIR}/generate_ps1_song_catalog.py"
			"${CMAKE_CURRENT_SOURCE_DIR}/convert_bopeebo_to_vagi.py"
			"${CMAKE_CURRENT_SOURCE_DIR}/convert_bopeebo_visuals.py"
			"${CMAKE_CURRENT_SOURCE_DIR}/animate_preview.py")
		foreach(_song cocoa eggnog winter-horrorland)
			list(APPEND _week5_dependencies
				"${FUNKIN_PS1_ASSETS_DIR}/preload/data/songs/${_song}/${_song}-chart.json"
				"${FUNKIN_PS1_ASSETS_DIR}/preload/data/songs/${_song}/${_song}-metadata.json")
		endforeach()
		foreach(_song cocoa eggnog)
			list(APPEND _week5_dependencies
				"${FUNKIN_PS1_ASSETS_DIR}/songs/${_song}/Inst.ogg"
				"${FUNKIN_PS1_ASSETS_DIR}/songs/${_song}/Voices-bf.ogg"
				"${FUNKIN_PS1_ASSETS_DIR}/songs/${_song}/Voices-parents-christmas.ogg")
		endforeach()
	list(APPEND _week5_dependencies
			"${FUNKIN_PS1_ASSETS_DIR}/songs/winter-horrorland/Inst.ogg"
			"${FUNKIN_PS1_ASSETS_DIR}/songs/winter-horrorland/Voices-bf.ogg"
			"${FUNKIN_PS1_ASSETS_DIR}/songs/winter-horrorland/Voices-monster.ogg"
			"${FUNKIN_PS1_ASSETS_DIR}/week5/images/christmas/bgWalls.png"
			"${FUNKIN_PS1_ASSETS_DIR}/week5/images/christmas/bgEscalator.png"
			"${FUNKIN_PS1_ASSETS_DIR}/week5/images/christmas/christmasTree.png"
			"${FUNKIN_PS1_ASSETS_DIR}/week5/images/christmas/fgSnow.png"
			"${FUNKIN_PS1_ASSETS_DIR}/week5/images/christmas/santa.png"
			"${FUNKIN_PS1_ASSETS_DIR}/week5/images/christmas/santa.xml"
			"${FUNKIN_PS1_ASSETS_DIR}/week5/images/christmas/evilBG.png"
			"${FUNKIN_PS1_ASSETS_DIR}/week5/images/christmas/evilTree.png"
			"${FUNKIN_PS1_ASSETS_DIR}/week5/images/christmas/evilSnow.png"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/parents-christmas/Animation.json"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/parents-christmas/spritemap1.json"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/parents-christmas/spritemap1.png"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/monster/Animation.json"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/monster/spritemap1.json"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/monster/spritemap1.png"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/gf-christmas/Animation.json"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/gf-christmas/spritemap1.json"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/gf-christmas/spritemap1.png")
		add_custom_command(
			OUTPUT "${_week5_header}" "${_week5_visual_header}" "${_week5_scene}"
				${_week5_audio_outputs} ${_week5_chart_outputs}
			COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/generate_ps1_week5_assets.py"
				--assets "${FUNKIN_PS1_ASSETS_DIR}" --ffmpeg "${FUNKIN_PS1_FFMPEG}"
				--output-dir "${_week5_audio_dir}" --header "${_week5_header}"
				--chart-dir "${_week5_chart_dir}" --scene "${_week5_scene}"
				--visual-header "${_week5_visual_header}"
			DEPENDS ${_week5_dependencies}
			VERBATIM)
	endif()
	# Week 6 classic songs use their own four-channel VAGi, chart bank, pixel stage,
	# characters, pixel arrows and CLUT. Existing week packages are copied as-is.
	set(_week6_audio_dir "${CMAKE_CURRENT_BINARY_DIR}/week6-audio")
	set(_week6_chart_dir "${_week6_audio_dir}/charts")
	set(_week6_header "${CMAKE_CURRENT_BINARY_DIR}/week6_catalog.h")
	set(_week6_visual_header "${CMAKE_CURRENT_BINARY_DIR}/week6_visual_data.h")
	set(_week6_scene "${CMAKE_CURRENT_BINARY_DIR}/week6-scene.bin")
	set(_week6_audio_outputs
		"${_week6_audio_dir}/senpai.vag"
		"${_week6_audio_dir}/roses.vag"
		"${_week6_audio_dir}/thorns.vag")
	set(_week6_chart_outputs)
	foreach(_song_code SEN ROS THO)
		foreach(_difficulty E N H)
			list(APPEND _week6_chart_outputs "${_week6_chart_dir}/${_song_code}${_difficulty}.BIN")
		endforeach()
	endforeach()
	if(FUNKIN_PS1_PRECONVERTED_WEEK6_DIR)
		set(_week6_package_files
			week6_catalog.h week6_visual_data.h week6-scene.bin
			week6-audio/senpai.vag week6-audio/roses.vag week6-audio/thorns.vag
			week6-audio/charts/SENE.BIN week6-audio/charts/SENN.BIN week6-audio/charts/SENH.BIN
			week6-audio/charts/ROSE.BIN week6-audio/charts/ROSN.BIN week6-audio/charts/ROSH.BIN
			week6-audio/charts/THOE.BIN week6-audio/charts/THON.BIN week6-audio/charts/THOH.BIN)
		foreach(_week6_package_file IN LISTS _week6_package_files)
			if(NOT EXISTS "${FUNKIN_PS1_PRECONVERTED_WEEK6_DIR}/${_week6_package_file}")
				message(FATAL_ERROR "Missing reusable Week 6 package file: ${FUNKIN_PS1_PRECONVERTED_WEEK6_DIR}/${_week6_package_file}")
			endif()
			get_filename_component(_week6_destination_dir "${CMAKE_CURRENT_BINARY_DIR}/${_week6_package_file}" DIRECTORY)
			file(MAKE_DIRECTORY "${_week6_destination_dir}")
			configure_file("${FUNKIN_PS1_PRECONVERTED_WEEK6_DIR}/${_week6_package_file}"
				"${CMAKE_CURRENT_BINARY_DIR}/${_week6_package_file}" COPYONLY)
		endforeach()
	else()
		set(_week6_dependencies
			"${CMAKE_CURRENT_SOURCE_DIR}/generate_ps1_week6_assets.py"
			"${CMAKE_CURRENT_SOURCE_DIR}/generate_ps1_song_catalog.py"
			"${CMAKE_CURRENT_SOURCE_DIR}/convert_bopeebo_to_vagi.py"
			"${CMAKE_CURRENT_SOURCE_DIR}/convert_bopeebo_visuals.py")
		foreach(_song senpai roses thorns)
			list(APPEND _week6_dependencies
				"${FUNKIN_PS1_ASSETS_DIR}/preload/data/songs/${_song}/${_song}-chart.json"
				"${FUNKIN_PS1_ASSETS_DIR}/preload/data/songs/${_song}/${_song}-metadata.json"
				"${FUNKIN_PS1_ASSETS_DIR}/songs/${_song}/Inst.ogg"
				"${FUNKIN_PS1_ASSETS_DIR}/songs/${_song}/Voices-bf.ogg")
		endforeach()
	list(APPEND _week6_dependencies
			"${FUNKIN_PS1_ASSETS_DIR}/songs/senpai/Voices-senpai.ogg"
			"${FUNKIN_PS1_ASSETS_DIR}/songs/roses/Voices-senpai.ogg"
			"${FUNKIN_PS1_ASSETS_DIR}/songs/thorns/Voices-spirit.ogg"
			"${FUNKIN_PS1_ASSETS_DIR}/week6/images/weeb/weebSky.png"
			"${FUNKIN_PS1_ASSETS_DIR}/week6/images/weeb/weebBackTrees.png"
			"${FUNKIN_PS1_ASSETS_DIR}/week6/images/weeb/weebSchool.png"
			"${FUNKIN_PS1_ASSETS_DIR}/week6/images/weeb/weebStreet.png"
			"${FUNKIN_PS1_ASSETS_DIR}/week6/images/weeb/weebTreesBack.png"
			"${FUNKIN_PS1_ASSETS_DIR}/week6/images/weeb/bgFreaks.png"
			"${FUNKIN_PS1_ASSETS_DIR}/week6/images/weeb/bgFreaks.xml"
			"${FUNKIN_PS1_ASSETS_DIR}/week6/images/weeb/evil/weebBackTrees.png"
			"${FUNKIN_PS1_ASSETS_DIR}/week6/images/weeb/evil/weebSchool.png"
			"${FUNKIN_PS1_ASSETS_DIR}/week6/images/weeb/evil/weebStreet.png"
			"${FUNKIN_PS1_ASSETS_DIR}/week6/images/weeb/evil/weebTrees.png"
			"${FUNKIN_PS1_ASSETS_DIR}/week6/images/weeb/pixelUI/arrows-pixels.png"
			"${FUNKIN_PS1_ASSETS_DIR}/week6/images/weeb/pixelUI/arrows-pixels.xml"
			"${FUNKIN_PS1_ASSETS_DIR}/preload/data/stages/school.json"
			"${FUNKIN_PS1_ASSETS_DIR}/preload/data/stages/schoolEvil.json"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/senpai.png"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/senpai.xml"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/bfPixel.png"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/bfPixel.xml"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/gfPixel.png"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/gfPixel.xml"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/spirit.png"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/spirit.txt"
			"${FUNKIN_PS1_ASSETS_DIR}/preload/images/icons/icon-senpai.png"
			"${FUNKIN_PS1_ASSETS_DIR}/preload/images/icons/icon-senpai-angry.png"
			"${FUNKIN_PS1_ASSETS_DIR}/preload/images/icons/icon-spirit.png")
		add_custom_command(
			OUTPUT "${_week6_header}" "${_week6_visual_header}" "${_week6_scene}"
				${_week6_audio_outputs} ${_week6_chart_outputs}
			COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/generate_ps1_week6_assets.py"
				--assets "${FUNKIN_PS1_ASSETS_DIR}" --ffmpeg "${FUNKIN_PS1_FFMPEG}"
				--output-dir "${_week6_audio_dir}" --header "${_week6_header}"
				--chart-dir "${_week6_chart_dir}" --scene "${_week6_scene}"
				--visual-header "${_week6_visual_header}"
			DEPENDS ${_week6_dependencies}
			VERBATIM)
	endif()
	# Week 7 classic songs use their own four-channel VAGi and chart files.
	# The compact 3-page battlefield/actor package is loaded on demand.
	set(_week7_audio_dir "${CMAKE_CURRENT_BINARY_DIR}/week7-audio")
	set(_week7_chart_dir "${_week7_audio_dir}/charts")
	set(_week7_header "${CMAKE_CURRENT_BINARY_DIR}/week7_catalog.h")
	set(_week7_visual_header "${CMAKE_CURRENT_BINARY_DIR}/week7_visual_data.h")
	set(_week7_scene "${CMAKE_CURRENT_BINARY_DIR}/week7-scene.bin")
	set(_week7_audio_outputs
		"${_week7_audio_dir}/ugh.vag"
		"${_week7_audio_dir}/guns.vag"
		"${_week7_audio_dir}/stress.vag")
	set(_week7_chart_outputs)
	foreach(_song_code UGH GUN STR)
		foreach(_difficulty E N H)
			list(APPEND _week7_chart_outputs "${_week7_chart_dir}/${_song_code}${_difficulty}.BIN")
		endforeach()
	endforeach()
	if(FUNKIN_PS1_PRECONVERTED_WEEK7_DIR)
		set(_week7_package_files
			week7_catalog.h week7_visual_data.h week7-scene.bin
			week7-audio/ugh.vag week7-audio/guns.vag week7-audio/stress.vag
			week7-audio/charts/UGHE.BIN week7-audio/charts/UGHN.BIN week7-audio/charts/UGHH.BIN
			week7-audio/charts/GUNE.BIN week7-audio/charts/GUNN.BIN week7-audio/charts/GUNH.BIN
			week7-audio/charts/STRE.BIN week7-audio/charts/STRN.BIN week7-audio/charts/STRH.BIN)
		foreach(_week7_package_file IN LISTS _week7_package_files)
			if(NOT EXISTS "${FUNKIN_PS1_PRECONVERTED_WEEK7_DIR}/${_week7_package_file}")
				message(FATAL_ERROR "Missing reusable Week 7 package file: ${FUNKIN_PS1_PRECONVERTED_WEEK7_DIR}/${_week7_package_file}")
			endif()
			get_filename_component(_week7_destination_dir "${CMAKE_CURRENT_BINARY_DIR}/${_week7_package_file}" DIRECTORY)
			file(MAKE_DIRECTORY "${_week7_destination_dir}")
			configure_file("${FUNKIN_PS1_PRECONVERTED_WEEK7_DIR}/${_week7_package_file}"
				"${CMAKE_CURRENT_BINARY_DIR}/${_week7_package_file}" COPYONLY)
		endforeach()
	else()
		set(_week7_dependencies
			"${CMAKE_CURRENT_SOURCE_DIR}/generate_ps1_week7_assets.py"
			"${CMAKE_CURRENT_SOURCE_DIR}/generate_ps1_song_catalog.py"
			"${CMAKE_CURRENT_SOURCE_DIR}/convert_bopeebo_to_vagi.py"
			"${CMAKE_CURRENT_SOURCE_DIR}/convert_bopeebo_visuals.py"
			"${CMAKE_CURRENT_SOURCE_DIR}/animate_preview.py")
		foreach(_song ugh guns stress)
			list(APPEND _week7_dependencies
				"${FUNKIN_PS1_ASSETS_DIR}/preload/data/songs/${_song}/${_song}-chart.json"
				"${FUNKIN_PS1_ASSETS_DIR}/preload/data/songs/${_song}/${_song}-metadata.json"
				"${FUNKIN_PS1_ASSETS_DIR}/songs/${_song}/Inst.ogg"
				"${FUNKIN_PS1_ASSETS_DIR}/songs/${_song}/Voices-bf.ogg"
				"${FUNKIN_PS1_ASSETS_DIR}/songs/${_song}/Voices-tankman.ogg")
		endforeach()
	list(APPEND _week7_dependencies
			"${FUNKIN_PS1_ASSETS_DIR}/week7/images/tankSky.png"
			"${FUNKIN_PS1_ASSETS_DIR}/week7/images/mountains2.png"
			"${FUNKIN_PS1_ASSETS_DIR}/week7/images/tankBuildings.png"
			"${FUNKIN_PS1_ASSETS_DIR}/week7/images/cityruins2.png"
			"${FUNKIN_PS1_ASSETS_DIR}/week7/images/tankGround.png"
			"${FUNKIN_PS1_ASSETS_DIR}/week7/images/bricksGround.png"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/tankman/basic/Animation.json"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/tankman/basic/spritemap1.json"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/tankman/basic/spritemap1.png"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/bf/Animation.json"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/bf/spritemap1.json"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/bf/spritemap1.png"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/gfTankmen.xml"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/gfTankmen.png"
			"${FUNKIN_PS1_ASSETS_DIR}/preload/images/icons/icon-tankman.png"
			"${FUNKIN_PS1_ASSETS_DIR}/preload/images/icons/icon-bf.png")
		add_custom_command(
			OUTPUT "${_week7_header}" "${_week7_visual_header}" "${_week7_scene}"
				${_week7_audio_outputs} ${_week7_chart_outputs}
			COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/generate_ps1_week7_assets.py"
				--assets "${FUNKIN_PS1_ASSETS_DIR}" --ffmpeg "${FUNKIN_PS1_FFMPEG}"
				--output-dir "${_week7_audio_dir}" --header "${_week7_header}"
				--chart-dir "${_week7_chart_dir}" --scene "${_week7_scene}"
				--visual-header "${_week7_visual_header}"
			DEPENDS ${_week7_dependencies}
			VERBATIM)
	endif()
	# WeekEnd 1 classic songs are generated independently. Erect and Spaghetti
	# are intentionally not part of this catalog/build.
	set(_weekend1_audio_dir "${CMAKE_CURRENT_BINARY_DIR}/weekend1-audio")
	set(_weekend1_chart_dir "${_weekend1_audio_dir}/charts")
	set(_weekend1_header "${CMAKE_CURRENT_BINARY_DIR}/weekend1_catalog.h")
	set(_weekend1_visual_header "${CMAKE_CURRENT_BINARY_DIR}/weekend1_visual_data.h")
	set(_weekend1_scene "${CMAKE_CURRENT_BINARY_DIR}/weekend1-scene.bin")
	set(_weekend1_audio_outputs
		"${_weekend1_audio_dir}/darnell.vag" "${_weekend1_audio_dir}/litup.vag"
		"${_weekend1_audio_dir}/2hot.vag" "${_weekend1_audio_dir}/blazin.vag")
	set(_weekend1_chart_outputs)
	foreach(_song_code DNL LIT 2HT BLZ)
		foreach(_difficulty E N H)
			list(APPEND _weekend1_chart_outputs "${_weekend1_chart_dir}/${_song_code}${_difficulty}.BIN")
		endforeach()
	endforeach()
	if(FUNKIN_PS1_PRECONVERTED_WEEKEND1_DIR)
		set(_weekend1_package_files
			weekend1_catalog.h weekend1_visual_data.h weekend1-scene.bin
			weekend1-audio/darnell.vag weekend1-audio/litup.vag
			weekend1-audio/2hot.vag weekend1-audio/blazin.vag
			weekend1-audio/charts/DNLE.BIN weekend1-audio/charts/DNLN.BIN weekend1-audio/charts/DNLH.BIN
			weekend1-audio/charts/LITE.BIN weekend1-audio/charts/LITN.BIN weekend1-audio/charts/LITH.BIN
			weekend1-audio/charts/2HTE.BIN weekend1-audio/charts/2HTN.BIN weekend1-audio/charts/2HTH.BIN
			weekend1-audio/charts/BLZE.BIN weekend1-audio/charts/BLZN.BIN weekend1-audio/charts/BLZH.BIN)
		foreach(_weekend1_package_file IN LISTS _weekend1_package_files)
			if(NOT EXISTS "${FUNKIN_PS1_PRECONVERTED_WEEKEND1_DIR}/${_weekend1_package_file}")
				message(FATAL_ERROR "Missing reusable WeekEnd 1 package file: ${FUNKIN_PS1_PRECONVERTED_WEEKEND1_DIR}/${_weekend1_package_file}")
			endif()
			get_filename_component(_weekend1_destination_dir "${CMAKE_CURRENT_BINARY_DIR}/${_weekend1_package_file}" DIRECTORY)
			file(MAKE_DIRECTORY "${_weekend1_destination_dir}")
			configure_file("${FUNKIN_PS1_PRECONVERTED_WEEKEND1_DIR}/${_weekend1_package_file}"
				"${CMAKE_CURRENT_BINARY_DIR}/${_weekend1_package_file}" COPYONLY)
		endforeach()
	else()
		set(_weekend1_dependencies
			"${CMAKE_CURRENT_SOURCE_DIR}/generate_ps1_weekend1_assets.py"
			"${CMAKE_CURRENT_SOURCE_DIR}/generate_ps1_song_catalog.py"
			"${CMAKE_CURRENT_SOURCE_DIR}/convert_bopeebo_to_vagi.py"
			"${CMAKE_CURRENT_SOURCE_DIR}/convert_bopeebo_visuals.py"
			"${CMAKE_CURRENT_SOURCE_DIR}/animate_preview.py")
		foreach(_song darnell lit-up 2hot blazin)
			list(APPEND _weekend1_dependencies
				"${FUNKIN_PS1_ASSETS_DIR}/preload/data/songs/${_song}/${_song}-chart.json"
				"${FUNKIN_PS1_ASSETS_DIR}/preload/data/songs/${_song}/${_song}-metadata.json"
				"${FUNKIN_PS1_ASSETS_DIR}/songs/${_song}/Inst.ogg")
		endforeach()
		foreach(_stem Voices-pico.ogg Voices-darnell.ogg)
			foreach(_song darnell lit-up 2hot)
				list(APPEND _weekend1_dependencies "${FUNKIN_PS1_ASSETS_DIR}/songs/${_song}/${_stem}")
			endforeach()
		endforeach()
		list(APPEND _weekend1_dependencies
			"${FUNKIN_PS1_ASSETS_DIR}/weekend1/images/phillyStreets/phillySkybox.png"
			"${FUNKIN_PS1_ASSETS_DIR}/weekend1/images/phillyStreets/phillySkyline.png"
			"${FUNKIN_PS1_ASSETS_DIR}/weekend1/images/phillyStreets/phillyHighway.png"
			"${FUNKIN_PS1_ASSETS_DIR}/weekend1/images/phillyStreets/phillyForegroundCity.png"
			"${FUNKIN_PS1_ASSETS_DIR}/weekend1/images/phillyStreets/phillyConstruction.png"
			"${FUNKIN_PS1_ASSETS_DIR}/weekend1/images/phillyStreets/phillyForeground.png"
			"${FUNKIN_PS1_ASSETS_DIR}/weekend1/images/phillyBlazin/skyBlur.png"
			"${FUNKIN_PS1_ASSETS_DIR}/weekend1/images/phillyBlazin/streetBlur.png"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/pico/basic-animations/Animation.json"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/pico/basic-animations/spritemap1.json"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/pico/basic-animations/spritemap1.png"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/darnell/Animation.json"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/darnell/spritemap1.json"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/darnell/spritemap1.png"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/nene/Animation.json"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/nene/spritemap1.json"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/nene/spritemap1.png"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/picoBlazin/Animation.json"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/picoBlazin/spritemap1.json"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/picoBlazin/spritemap1.png"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/darnellBlazin/Animation.json"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/darnellBlazin/spritemap1.json"
			"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/darnellBlazin/spritemap1.png"
			"${FUNKIN_PS1_ASSETS_DIR}/preload/images/icons/icon-pico.png"
			"${FUNKIN_PS1_ASSETS_DIR}/preload/images/icons/icon-darnell.png")
		add_custom_command(
			OUTPUT "${_weekend1_header}" "${_weekend1_visual_header}" "${_weekend1_scene}"
				${_weekend1_audio_outputs} ${_weekend1_chart_outputs}
			COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/generate_ps1_weekend1_assets.py"
				--assets "${FUNKIN_PS1_ASSETS_DIR}" --ffmpeg "${FUNKIN_PS1_FFMPEG}"
				--output-dir "${_weekend1_audio_dir}" --header "${_weekend1_header}"
				--chart-dir "${_weekend1_chart_dir}" --scene "${_weekend1_scene}"
				--visual-header "${_weekend1_visual_header}"
			DEPENDS ${_weekend1_dependencies}
			VERBATIM)
	endif()
	configure_file("${FUNKIN_PS1_AUDIO_VAGI_BOPEEBO_4CH}"
		"${CMAKE_CURRENT_BINARY_DIR}/stream-playable.vag" COPYONLY)
	set(_menu_audio_header "${CMAKE_CURRENT_BINARY_DIR}/menu_audio_data.h")
	set(_menu_audio_vagi "${CMAKE_CURRENT_BINARY_DIR}/menu.vag")
	set(_gameover_loop_vagi "${CMAKE_CURRENT_BINARY_DIR}/gameover-loop.vag")
	set(_gameover_end_vagi "${CMAKE_CURRENT_BINARY_DIR}/gameover-end.vag")
	if(FUNKIN_PS1_PRECONVERTED_BASE_DIR)
		foreach(_base_package_file menu_audio_data.h menu.vag gameover-loop.vag gameover-end.vag)
			if(NOT EXISTS "${FUNKIN_PS1_PRECONVERTED_BASE_DIR}/${_base_package_file}")
				message(FATAL_ERROR "Missing reusable base package file: ${FUNKIN_PS1_PRECONVERTED_BASE_DIR}/${_base_package_file}")
			endif()
			configure_file("${FUNKIN_PS1_PRECONVERTED_BASE_DIR}/${_base_package_file}"
				"${CMAKE_CURRENT_BINARY_DIR}/${_base_package_file}" COPYONLY)
		endforeach()
	else()
		add_custom_command(
			OUTPUT "${_menu_audio_header}" "${_menu_audio_vagi}"
				"${_gameover_loop_vagi}" "${_gameover_end_vagi}"
			COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/generate_ps1_menu_audio.py"
				--ffmpeg "${FUNKIN_PS1_FFMPEG}"
				--assets "${FUNKIN_PS1_ASSETS_DIR}"
				--music "${_menu_audio_vagi}"
				--gameover-loop "${_gameover_loop_vagi}"
				--gameover-end "${_gameover_end_vagi}"
				--header "${_menu_audio_header}"
			DEPENDS generate_ps1_menu_audio.py convert_bopeebo_to_vagi.py ${_visual_asset_dependencies}
			VERBATIM
		)
	endif()
	set(_playable_sources spu_probe.c "${_psn00bsdk_cdstream_dir}/stream.c")
	if(FUNKIN_PS1_STARTUP_BEFORE_BSS_MARKER AND FUNKIN_PS1_STARTUP_AFTER_BSS_MARKER)
		message(FATAL_ERROR "Select only one startup marker position")
	elseif(FUNKIN_PS1_STARTUP_BEFORE_BSS_MARKER)
		list(APPEND _playable_sources startup_before_bss_marker.c)
	elseif(FUNKIN_PS1_STARTUP_AFTER_BSS_MARKER)
		list(APPEND _playable_sources startup_after_bss_marker.c)
	endif()
	psn00bsdk_add_executable(funkin-ps1-bopeebo-playable GPREL
		${_playable_sources}
		"${_playable_chart_header}" "${_playable_visual_header}"
		"${_menu_audio_header}" "${_week4_header}" "${_week4_visual_header}"
		"${_week5_header}" "${_week5_visual_header}"
		"${_week6_header}" "${_week6_visual_header}"
		"${_week7_header}" "${_week7_visual_header}"
		"${_weekend1_header}" "${_weekend1_visual_header}")
	add_custom_target(funkin-ps1-menu-audio DEPENDS "${_menu_audio_header}" "${_menu_audio_vagi}"
		"${_gameover_loop_vagi}" "${_gameover_end_vagi}")
	add_dependencies(funkin-ps1-bopeebo-playable funkin-ps1-menu-audio)
	add_custom_target(funkin-ps1-week5-assets DEPENDS "${_week5_header}"
		"${_week5_visual_header}" "${_week5_scene}" ${_week5_audio_outputs} ${_week5_chart_outputs})
	add_dependencies(funkin-ps1-bopeebo-playable funkin-ps1-week5-assets)
	add_custom_target(funkin-ps1-week6-assets DEPENDS "${_week6_header}"
		"${_week6_visual_header}" "${_week6_scene}" ${_week6_audio_outputs} ${_week6_chart_outputs})
	add_dependencies(funkin-ps1-bopeebo-playable funkin-ps1-week6-assets)
	add_custom_target(funkin-ps1-week7-assets DEPENDS "${_week7_header}"
		"${_week7_visual_header}" "${_week7_scene}" ${_week7_audio_outputs} ${_week7_chart_outputs})
	add_dependencies(funkin-ps1-bopeebo-playable funkin-ps1-week7-assets)
	add_custom_target(funkin-ps1-weekend1-assets DEPENDS "${_weekend1_header}"
		"${_weekend1_visual_header}" "${_weekend1_scene}"
		${_weekend1_audio_outputs} ${_weekend1_chart_outputs})
	add_dependencies(funkin-ps1-bopeebo-playable funkin-ps1-weekend1-assets)
	target_compile_definitions(funkin-ps1-bopeebo-playable PRIVATE
		TEST_CHANNELS=4 TEST_BOPEEBO_4CH=1 TEST_PLAYABLE_BOPEEBO=1
		GAME_DAD_LANES_DEFAULT=$<BOOL:${FUNKIN_PS1_DAD_LANES_DEFAULT}>
		GAME_DIAGNOSTICS_DEFAULT=$<BOOL:${FUNKIN_PS1_DIAGNOSTICS_DEFAULT}>
		GAME_ARROW_DIAGNOSTIC_DEFAULT=$<BOOL:${FUNKIN_PS1_ARROW_DIAGNOSTIC_DEFAULT}>
		GAME_JUDGEMENT_TEST_DEFAULT=$<BOOL:${FUNKIN_PS1_JUDGEMENT_TEST_DEFAULT}>
		GAME_JUDGEMENT_VISUAL_TEST_DEFAULT=$<BOOL:${FUNKIN_PS1_JUDGEMENT_VISUAL_TEST_DEFAULT}>
		GAME_JUDGEMENT_SOLID_PROBE_DEFAULT=$<BOOL:${FUNKIN_PS1_JUDGEMENT_SOLID_PROBE_DEFAULT}>
		GAME_JUDGEMENT_TEXTURE_PROBE_DEFAULT=$<BOOL:${FUNKIN_PS1_JUDGEMENT_TEXTURE_PROBE_DEFAULT}>
		GAME_JUDGEMENT_CLUT_PROBE_DEFAULT=$<BOOL:${FUNKIN_PS1_JUDGEMENT_CLUT_PROBE_DEFAULT}>
		GAME_JUDGEMENT_POPUP_CLUT_PROBE_DEFAULT=$<BOOL:${FUNKIN_PS1_JUDGEMENT_POPUP_CLUT_PROBE_DEFAULT}>
		GAME_JUDGEMENT_POPUP_CLUT_RELOCATE_PROBE_DEFAULT=$<BOOL:${FUNKIN_PS1_JUDGEMENT_POPUP_CLUT_RELOCATE_PROBE_DEFAULT}>
		GAME_JUDGEMENT_POPUP_CLUT_SLOT_PROBE_DEFAULT=$<BOOL:${FUNKIN_PS1_JUDGEMENT_POPUP_CLUT_SLOT_PROBE_DEFAULT}>
		GAME_SCENE_DEMO_DEFAULT=$<BOOL:${FUNKIN_PS1_SCENE_DEMO_DEFAULT}>
		GAME_HEALTH_BAR_TEST_DEFAULT=$<BOOL:${FUNKIN_PS1_HEALTH_BAR_TEST_DEFAULT}>
		GAME_STARTUP_MAIN_MARKER=$<BOOL:${FUNKIN_PS1_STARTUP_MAIN_MARKER}>
		TEST_NO_LOOP=1 TEST_TOTAL_SAMPLES=3509453u)
	target_include_directories(funkin-ps1-bopeebo-playable PRIVATE
		"${_psn00bsdk_cdstream_dir}" "${CMAKE_CURRENT_BINARY_DIR}")
	psn00bsdk_add_cd_image(
		ps1-bopeebo-playable-disc funkin-ps1-bopeebo-playable
		bopeebo_playable_iso.xml
		DEPENDS funkin-ps1-bopeebo-playable system.cnf
			"${CMAKE_CURRENT_BINARY_DIR}/stream-playable.vag"
			"${_week2_visual_payload}"
			"${_week1_visual_payload}"
			"${_week3_visual_payload}"
			"${_week4_visual_payload}"
			"${_week5_scene}"
			"${_week6_scene}"
			"${_week7_scene}"
			"${_weekend1_scene}"
			${_song_audio_outputs}
			${_song_chart_outputs}
			${_week4_audio_outputs}
			${_week4_chart_outputs}
			${_week5_audio_outputs}
			${_week5_chart_outputs}
			${_week6_audio_outputs}
			${_week6_chart_outputs}
			${_week7_audio_outputs}
			${_week7_chart_outputs}
			${_weekend1_audio_outputs}
			${_weekend1_chart_outputs}
			"${_menu_audio_vagi}" "${_gameover_loop_vagi}" "${_gameover_end_vagi}")
elseif(DEFINED FUNKIN_PS1_BOPEEBO_CHART_JSON OR DEFINED FUNKIN_PS1_AUDIO_VAGI_BOPEEBO_4CH)
	message(FATAL_ERROR "Playable Bopeebo requires both FUNKIN_PS1_BOPEEBO_CHART_JSON and FUNKIN_PS1_AUDIO_VAGI_BOPEEBO_4CH to name existing files")
endif()

# Minimal diagnostic image: prove PS-X EXE/ISO startup and a solid GPU frame,
# independently from gameplay, audio, fonts, CD callbacks, and scene assets.
psn00bsdk_add_executable(funkin-ps1-boot-probe GPREL boot_probe.c)
psn00bsdk_add_cd_image(
	ps1-boot-probe-disc
	funkin-ps1-boot-probe
	boot_probe_iso.xml
	DEPENDS funkin-ps1-boot-probe system.cnf
)

if(DEFINED _week1_visual_payload)
# Incremental startup probe: read one verified scene page, transfer it and its
# official CLUT to VRAM, then draw a textured quad. It does not start gameplay.
	psn00bsdk_add_executable(funkin-ps1-startup-stage-probe GPREL
		startup_stage_probe.c "${_playable_visual_header}")
	target_include_directories(funkin-ps1-startup-stage-probe PRIVATE "${CMAKE_CURRENT_BINARY_DIR}")
	psn00bsdk_add_cd_image(
		ps1-startup-stage-probe-disc
		funkin-ps1-startup-stage-probe
		startup_stage_probe_iso.xml
		DEPENDS funkin-ps1-startup-stage-probe system.cnf
			"${_week1_visual_payload}" "${_playable_visual_header}"
	)
endif()
