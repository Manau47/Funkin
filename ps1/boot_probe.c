#include <stdint.h>
#include <psxapi.h>
#include <psxgpu.h>

#define SCREEN_W 320
#define SCREEN_H 240

int main(void)
{
	DISPENV display;
	DRAWENV draw;
	FILL fill;

	ResetGraph(0);
	SetDefDrawEnv(&draw, 0, 0, SCREEN_W, SCREEN_H);
	SetDefDispEnv(&display, 0, 0, SCREEN_W, SCREEN_H);
	PutDrawEnv(&draw);
	PutDispEnv(&display);

	/* One synchronous solid GPU primitive; no font, CD, SPU, pad, or assets. */
	setFill(&fill);
	setRGB0(&fill, 32, 96, 160);
	setXY0(&fill, 0, 0);
	setWH(&fill, SCREEN_W, SCREEN_H);
	DrawPrim((uint32_t *)&fill);
	DrawSync(0);
	SetDispMask(1);

	for (;;) VSync(0);
	return 0;
}

