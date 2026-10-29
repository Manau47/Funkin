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
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/ui/popup/funkin/sick.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/ui/popup/funkin/good.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/ui/popup/funkin/bad.png"
		"${FUNKIN_PS1_ASSETS_DIR}/preload/images/ui/popup/funkin/shit.png")
	list(APPEND _visual_asset_dependencies
		"${FUNKIN_PS1_ASSETS_DIR}/preload/data/stages/spookyMansion.json"
		"${FUNKIN_PS1_ASSETS_DIR}/week2/images/halloween_bg/spritemap1.json"
		"${FUNKIN_PS1_ASSETS_DIR}/week2/images/halloween_bg/spritemap1.png"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/SpookyKids.xml"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/SpookyKids.png"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/monster/Animation.json"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/monster/spritemap1.json"
		"${FUNKIN_PS1_ASSETS_DIR}/shared/images/characters/monster/spritemap1.png"
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
	configure_file("${FUNKIN_PS1_AUDIO_VAGI_BOPEEBO_4CH}"
		"${CMAKE_CURRENT_BINARY_DIR}/stream-playable.vag" COPYONLY)
	set(_menu_audio_header "${CMAKE_CURRENT_BINARY_DIR}/menu_audio_data.h")
	set(_menu_audio_vagi "${CMAKE_CURRENT_BINARY_DIR}/menu.vag")
	set(_gameover_loop_vagi "${CMAKE_CURRENT_BINARY_DIR}/gameover-loop.vag")
	set(_gameover_end_vagi "${CMAKE_CURRENT_BINARY_DIR}/gameover-end.vag")
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
	set(_playable_sources spu_probe.c "${_psn00bsdk_cdstream_dir}/stream.c")
	if(FUNKIN_PS1_STARTUP_AFTER_BSS_MARKER)
		list(APPEND _playable_sources startup_after_bss_marker.c)
	endif()
	psn00bsdk_add_executable(funkin-ps1-bopeebo-playable GPREL
		${_playable_sources}
		"${_playable_chart_header}" "${_playable_visual_header}"
		"${_menu_audio_header}")
	add_custom_target(funkin-ps1-menu-audio DEPENDS "${_menu_audio_header}" "${_menu_audio_vagi}"
		"${_gameover_loop_vagi}" "${_gameover_end_vagi}")
	add_dependencies(funkin-ps1-bopeebo-playable funkin-ps1-menu-audio)
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
			${_song_audio_outputs}
			${_song_chart_outputs}
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

