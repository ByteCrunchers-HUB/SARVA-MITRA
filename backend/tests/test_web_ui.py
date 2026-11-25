from fastapi.testclient import TestClient
from backend.main import app

def test_web_ui_mounted():
    with TestClient(app) as client:
        # 1. UI Root
        res_ui = client.get("/ui/")
        assert res_ui.status_code == 200, res_ui.text
        assert "Sarva Mitra" in res_ui.text
        assert "mobile-bottom-nav" in res_ui.text
        assert "btn-mobile-menu" in res_ui.text
        assert "sidebar-overlay" in res_ui.text
        assert "manifest.json" in res_ui.text
        print("GET /ui/ returned mobile responsive webapp index.html: PASS")

        # 2. Stylesheet
        res_css = client.get("/ui/styles.css")
        assert res_css.status_code == 200
        assert "--primary-green" in res_css.text
        assert "mobile-bottom-nav" in res_css.text
        assert "sidebar.drawer-open" in res_css.text
        print("GET /ui/styles.css with mobile responsive rules: PASS")

        # 3. JavaScript
        res_js = client.get("/ui/app.js")
        assert res_js.status_code == 200
        assert "syncDashboardData" in res_js.text
        assert "openMobileDrawer" in res_js.text
        print("GET /ui/app.js: PASS")

        # 4. Web App Manifest
        res_manifest = client.get("/ui/manifest.json")
        assert res_manifest.status_code == 200
        assert "standalone" in res_manifest.text
        print("GET /ui/manifest.json (PWA WebApp manifest): PASS")

        # 5. Assets
        res_svg = client.get("/ui/assets/logo.svg")
        assert res_svg.status_code == 200
        print("GET /ui/assets/logo.svg: PASS")

        # 6. Redirect /app
        res_redir = client.get("/app", follow_redirects=False)
        assert res_redir.status_code == 307
        assert res_redir.headers["location"] == "/ui/"
        print("GET /app redirect to /ui/: PASS")

    print("\n=== ALL WEB UI MOUNT TESTS PASSED! ===")

if __name__ == "__main__":
    test_web_ui_mounted()
