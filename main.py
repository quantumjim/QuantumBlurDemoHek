import pew
import quantumblur as qb
from micromoth import QuantumCircuit
import math
import asyncio

import pics

pew.init()
screen = pew.Pix()

fps = 10
L = 32


def scroll(pix, dx=1):
    x = 0
    while True:
        for x in range(x, pix.width, dx):
            screen.box(0)
            screen.blit(pix, -x, 1)
            yield x
        x = -8


def draw_cursor(x, y, undraw=False):
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        if x + dx in range(L) and y + dy in range(L):
            if undraw:
                screen.pixel(x + dx, y + dy, 3 * height[x + dx + (y + dy) * L])
            else:
                screen.pixel(x + dx, y + dy, 2)
    pew.show(screen)


def draw_height(height):
    max_h = max(height) + 0.01
    for x in range(L):
        for y in range(L):
            h = height[x + y * L] / max_h
            b = int(h * pew.COLOR_NUM)
            if b == pew.COLOR_NUM:
                b = pew.COLOR_NUM - 1
            screen.pixel(x, y, b)
    pew.show(screen)


heights = [
    pics.hek,
    pics.cat,
    pics.kite,
    pics.moth,
    pics.lana,
]

async def main():

    while True:

        running = True
        theta = math.pi / 100
        last_idle = False
        ldX, ldY, ldb = 0, 0, 0
        log = False

        p = 0
        draw_height(heights[p])
        qc = qb.height2circuit(heights[p])
        gates = [['x', 0]]

        while running:

            rdX, rdY, rdb = 0, 0, None
            keys = pew.keys()
            if keys & pew.K_UP:
                rdY = +1
            elif keys & pew.K_DOWN:
                rdY = -1
            if keys & pew.K_LEFT:
                rdX = -1
            elif keys & pew.K_RIGHT:
                rdX = +1

            if keys & pew.K_O or keys & pew.K_X:
                if keys & pew.K_X:
                    rdb = 0
                else:
                    rdb = +1

            dX, dY, db = 0, 0, None
            if rdX != ldX:
                dX = rdX
            if rdY != ldY:
                dY = rdY
            if rdb != ldb:
                db = rdb

            ldX, ldY, ldb = rdX, rdY, rdb

            if db is not None:
                p = (p + rdb) % len(heights)
                draw_height(heights[p])
                qc = qb.height2circuit(heights[p])
                gates = [['x', 0]]

            if rdX:
                if gates[-1][0] == 'x':
                    gates[-1][1] += rdX
                else:
                    gates.append(['x', rdX])
            if rdY:
                if gates[-1][0] == 'x2':
                    gates[-1][1] += rdY
                else:
                    gates.append(['x2', rdY])

            qc_rot = QuantumCircuit(qc.num_qubits)
            reg = int(qc_rot.num_qubits / 2)
            for gate in gates:
                if gate[0] == 'x':
                    for q in range(reg):
                        qc_rot.cx(q, q + reg)
                        qc_rot.crx(gate[1] * theta, q + reg, q)
                        qc_rot.cx(q, q + reg)
                else:
                    for j in range(reg):
                        for q in [j, reg + j]:
                            qc_rot.rx(gate[1] * theta * 2 * 2**(-j), q)

            draw_height(qb.circuit2height(qc + qc_rot, log=log))

            pew.tick(1 / fps)
            
        await asyncio.sleep(0)

asyncio.run(main())

