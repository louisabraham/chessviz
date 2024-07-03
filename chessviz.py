import io
from collections import defaultdict
from math import cos, sin, pi

import chess.pgn
import requests


def board(game, SCALE=40):
    # https://static.displate.com/857x1200/displate/2021-04-14/12e39b1243b640bd6f31319e26e95ee0_d5a86c00358633ac6154b25d2d93a5a0.jpg

    board_white = "rgb(240,230,200)"
    board_black = "rgb(30,30,30)"
    white = "rgb(220, 130, 50)"
    black = "rgb(75, 70, 65)"

    def convert(uci):
        a, b, c, d = uci
        return ord(a) - ord("a"), int(b) - 1, ord(c) - ord("a"), int(d) - 1

    control = defaultdict(list)

    board = game.board()
    for i in range(64):
        control[i % 8, i // 8].append(board.color_at(i))

    black_moves = []
    white_moves = []

    for i, move in enumerate(game.mainline_moves()):
        board.push(move)

        moves = black_moves if i & 1 else white_moves
        x1, y1, x2, y2 = convert(move.uci())
        moves.append((x1, y1, x2, y2))
        if board.is_castling(move):
            assert y1 == y2
            if x2 == 6:
                x3 = 7
                x4 = 5
            else:
                assert x2 == 2
                x3 = 0
                x4 = 3
            moves.append((x3, y1, x4, y1))

        for i in range(64):
            control[i % 8, i // 8].append(board.color_at(i))

    def rect(x, y, w, h, color=None, style=""):
        if color is not None:
            style += "fill:" + color
        return f'<rect x="{SCALE*x}" y="{SCALE*y}" width="{SCALE*w}" height="{SCALE*h}" style="{style}"/>'

    def line(x1, y1, x2, y2, color, width):
        return (
            f'<line x1="{SCALE*x1}" y1="{SCALE*y1}" x2="{SCALE*x2}" y2="{SCALE*y2}" stroke="{color}" '
            f'stroke-width="{SCALE*width}" stroke-linecap="round"/>'
        )

    def circle(x, y, r, color):
        return f'<circle cx="{SCALE*x}" cy="{SCALE*y}" r="{SCALE*r}" fill="{color}"/>'

    def circle_contour(x, y, r, color, w):
        return f'<circle cx="{SCALE*x}" cy="{SCALE*y}" r="{SCALE*r}" stroke="{color}" stroke-width="{SCALE*w}"/>'

    def compress(l):
        if not l:
            return []
        ans = []
        x = l[0]
        c = 0
        for e in l:
            if e == x:
                c += 1
            else:
                ans.append((c, x))
                c = 1
                x = e
        ans.append((c, x))
        return ans

    def pie_chart(x, y, r, colors):
        n = len(colors)
        colors = compress(colors)
        if len(colors) == 1:
            return circle(x, y, r, colors[0][1])
        if colors[0][1] == colors[-1][1]:
            colors[-1][0] += 1
        ans = ""
        a = 0
        for cnt, color in colors:
            b = a + 2 * pi * (cnt + 0.1) / n
            ans += (
                f'<path fill="{color}" d="M {SCALE*(x+r*sin(a))} {SCALE*(y-r*cos(a))} '
                f"A {SCALE*r} {SCALE*r} 0 {b - a > pi:d} 1 {SCALE*(x+r*sin(b))} {SCALE*(y-r*cos(b))} "
                f'L {SCALE*x} {SCALE*y}"/>'
            )
            a += 2 * pi * cnt / n
        return ans

    def board_color(i, j):
        return board_white if (i + j) & 1 else board_black

    elements = []
    for i in range(8):
        for j in range(8):
            elements.append(rect(2 * i, 2 * (7 - j), 2, 2, board_color(i, j)))

    for moves, color in ((black_moves, black), (white_moves, white)):
        for x1, y1, x2, y2 in moves:
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            norm = (dx * dx + dy * dy) ** 0.5 / 0.05
            dx, dy = dy / norm, -dx / norm
            if color == black:
                dx = -dx
                dy = -dy
            elements.append(
                line(
                    2 * x1 + 1 + dx,
                    2 * (7 - y1) + 1 + dy,
                    2 * x2 + 1 + dx,
                    2 * (7 - y2) + 1 + dy,
                    color,
                    width=0.1,
                )
            )

    def last_player(colors):
        for c in reversed(colors):
            if c is not None:
                return c
        return None

    pie_color = {None: board_white, False: black, True: white}

    for (x, y), color in control.items():
        if last_player(color) is None:
            continue
        elements.append(
            circle_contour(
                2 * x + 1, 2 * (7 - y) + 1, 0.4, pie_color[last_player(color)], 0.2
            )
        )
        elements.append(
            pie_chart(
                2 * x + 1, 2 * (7 - y) + 1, 0.4, list(map(pie_color.__getitem__, color))
            )
        )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{16 * SCALE}" height="{16 * SCALE}">'
        + "".join(elements)
        + "</svg>"
    )


def get_game(gid):
    r = requests.get(
        "https://www.chessgames.com/perl/nph-chesspgn",
        params={"text": "1", "gid": gid},
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:127.0) Gecko/20100101 Firefox/127.0",
        },
    )
    assert r.status_code == 200
    return r.text


def main(gid):
    return board(chess.pgn.read_game(io.StringIO(get_game(gid))))


if __name__ == "__main__":
    import sys

    gid = sys.argv[1]

    print(main(gid))
