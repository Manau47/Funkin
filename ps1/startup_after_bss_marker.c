/*
 * Startup-only diagnostic for the playable target.
 *
 * PSn00bSDK v0.24's _start_inner() first zeroes [__bss_start, _end), then
 * initializes the heap, copies argv, calls constructors, and enters main.
 * This replacement intentionally performs only the first operation and
 * displays a fixed amber frame. The playable main and all game assets remain
 * linked, but are not entered in this diagnostic image.
 *
 * The startup sequence being checkpointed is documented in the SDK source
 * at Lameguy64/PSn00bSDK commit 06e65bea3a778b2dae5af77a7935ae3868ddd4d3.
 */

#include <stdint.h>
#include <psxapi.h>
#include <psxgpu.h>

#define STARTUP_MARKER_W 320
#define STARTUP_MARKER_H 240

extern int main(void);
extern uint8_t __bss_start[];
extern uint8_t _end[];

/* Keep the playable game's main section linked, but never take this path. */
static volatile uint32_t startup_release_code = 0xFFFFFFFFu;

void _start_inner(int argc, const char **argv)
{
	(void)argc;
	(void)argv;

	/* Match PSn00bSDK v0.24's word-wise BSS clear exactly. */
	for (uint32_t *cursor = (uint32_t *)__bss_start;
		 cursor < (uint32_t *)_end;
		 cursor++)
		*cursor = 0;

	/* Reached only after the actual game's linked BSS has been cleared. */
	DISPENV display;
	DRAWENV draw;
	FILL fill;
	ResetGraph(0);
	SetDefDrawEnv(&draw, 0, 0, STARTUP_MARKER_W, STARTUP_MARKER_H);
	SetDefDispEnv(&display, 0, 0, STARTUP_MARKER_W, STARTUP_MARKER_H);
	PutDrawEnv(&draw);
	PutDispEnv(&display);
	setFill(&fill);
	setRGB0(&fill, 255, 160, 0);
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
