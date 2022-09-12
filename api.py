from aiohttp import web

from chessviz import main


async def handle(request):
    gid = request.match_info.get("gid")
    ans = main(gid)
    return web.Response(body=ans, content_type="image/svg+xml")


async def make_app():
    app = web.Application(client_max_size=10 * 1024**2)
    app.add_routes([web.get("/{gid}", handle)])
    return app


if __name__ == "__main__":
    app = make_app()
    web.run_app(app)
