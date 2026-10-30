/*
 * Startup diagnostic that stops before clearing the linked executable BSS.
 * It uses the real playable target and keeps main linked, but never enters it.
 */

#include <stdint.h>
#include <psxapi.h>
#include <psxgpu.h>

#define STARTUP_MARKER_W 320
#define STARTUP_MARKER_H 240

extern int main(void);

/* Keep the real game code linked; this initialized gate remains nonzero. */
static volatile uint32_t startup_release_code = 0xFFFFFFFFu;

void _start_inner(int argc, const char **argv)
{
	(void)argc;
	(void)argv;

	DISPENV display;
	DRAWENV draw;
	FILL fill;
	/* Keep the BIOS GPU state in this probe; isolate ResetGraph separately. */
	SetDefDrawEnv(&draw, 0, 0, STARTUP_MARKER_W, STARTUP_MARKER_H);
	SetDefDispEnv(&display, 0, 0, STARTUP_MARKER_W, STARTUP_MARKER_H);
	PutDrawEnv(&draw);
	PutDispEnv(&display);
	setFill(&fill);
	setRGB0(&fill, 0, 255, 255);
	setXY0(&fill, 0, 0);
	setWH(&fill, STARTUP_MARKER_W, STARTUP_MARKER_H);
	DrawPrim((uint32_t *)&fill);
	DrawSync(0);
	SetDispMask(1);
	if (startup_release_code == 0u)
		(void)main();
	for (;;)
		VSync(0);
}
