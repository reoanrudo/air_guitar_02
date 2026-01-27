"""
Mobile UI Tests for VirtuTune

Tests for responsive design, touch targets, and mobile navigation.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()


class MobileUITestCase(TestCase):
    """Test mobile UI components and responsive design"""

    def setUp(self):
        """Set up test client and user"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_navigation_css_exists(self):
        """Test that navigation CSS file exists"""
        import os

        css_path = "static/css/navigation.css"
        self.assertTrue(os.path.exists(css_path), f"{css_path} does not exist")

    def test_navigation_js_exists(self):
        """Test that navigation JavaScript file exists"""
        import os

        js_path = "static/js/navigation.js"
        self.assertTrue(os.path.exists(js_path), f"{js_path} does not exist")

    def test_guitar_page_has_navigation(self):
        """Test that guitar template includes navigation"""
        with open("apps/guitar/templates/guitar/guitar.html", "r") as f:
            content = f.read()

        # Check that it extends base template (which has navigation)
        self.assertIn('extends "core/base.html"', content)

    def test_progress_page_has_navigation(self):
        """Test that progress template includes navigation"""
        with open("apps/progress/templates/progress/progress.html", "r") as f:
            content = f.read()

        # Check that it extends base template (which has navigation)
        self.assertIn('extends "core/base.html"', content)

    def test_base_template_has_viewport_meta(self):
        """Test that base template includes proper viewport meta tag"""
        with open("apps/core/templates/core/base.html", "r") as f:
            content = f.read()

        # Check for viewport meta tag
        self.assertIn('name="viewport"', content)
        self.assertIn("width=device-width", content)
        self.assertIn("initial-scale=1.0", content)

    def test_navigation_links_accessible(self):
        """Test that base template has all navigation links"""
        with open("apps/core/templates/core/base.html", "r") as f:
            content = f.read()

        # Check for main navigation links
        self.assertIn('href="/"', content)  # Home
        self.assertIn('href="/guitar/"', content)  # Guitar
        self.assertIn('href="/progress/"', content)  # Progress
        self.assertIn('href="/users/profile/"', content)  # Profile

    def test_mobile_menu_structure(self):
        """Test that base template has mobile menu structure"""
        with open("apps/core/templates/core/base.html", "r") as f:
            content = f.read()

        # Check for hamburger menu elements
        self.assertIn("navbar-toggle", content)
        self.assertIn("navbar-toggle-line", content)
        self.assertIn("navbar-mobile-menu", content)
        self.assertIn("navbar-overlay", content)

    def test_responsive_css_breakpoints(self):
        """Test that responsive CSS includes proper breakpoints"""
        with open("static/css/styles.css", "r") as f:
            css_content = f.read()

        # Check for mobile breakpoints
        self.assertIn("@media (max-width: 768px)", css_content)
        self.assertIn("@media (max-width: 767px)", css_content)
        self.assertIn("@media (max-width: 374px)", css_content)

    def test_guitar_mobile_css(self):
        """Test that guitar CSS includes mobile-specific styles"""
        with open("static/css/guitar.css", "r") as f:
            css_content = f.read()

        # Check for mobile breakpoint
        self.assertIn("@media (max-width: 767px)", css_content)

        # Check for vertical string layout on mobile
        self.assertIn("position: relative", css_content)
        self.assertIn("height: 50px", css_content)

    def test_progress_mobile_css(self):
        """Test that progress CSS includes mobile-specific styles"""
        with open("static/css/progress.css", "r") as f:
            css_content = f.read()

        # Check for mobile breakpoint
        self.assertIn("@media (max-width: 767px)", css_content)

        # Check for single column stats grid
        self.assertIn("grid-template-columns: 1fr", css_content)

    def test_touch_target_sizes(self):
        """Test that buttons meet minimum touch target size (44px)"""
        with open("static/css/styles.css", "r") as f:
            css_content = f.read()

        # Check for minimum touch target sizes
        self.assertIn("min-height: 44px", css_content)
        self.assertIn("min-width: 44px", css_content)

    def test_navigation_touch_targets(self):
        """Test that navigation elements meet touch target requirements"""
        with open("static/css/navigation.css", "r") as f:
            css_content = f.read()

        # Check for touch-friendly sizing
        self.assertIn("width: 44px", css_content)
        self.assertIn("height: 44px", css_content)
        self.assertIn("padding: 16px 20px", css_content)  # Chord buttons

    def test_css_syntax_validity(self):
        """Test that CSS files have matching braces"""
        css_files = [
            "static/css/styles.css",
            "static/css/guitar.css",
            "static/css/progress.css",
            "static/css/navigation.css",
        ]

        for css_file in css_files:
            with open(css_file, "r") as f:
                content = f.read()

            open_braces = content.count("{")
            close_braces = content.count("}")

            self.assertEqual(
                open_braces,
                close_braces,
                f"{css_file} has mismatched braces: "
                f"{open_braces} open, {close_braces} close",
            )

    def test_navigation_javascript_exists(self):
        """Test that navigation JavaScript file exists and is valid"""
        with open("static/js/navigation.js", "r") as f:
            js_content = f.read()

        # Check for key functionality
        self.assertIn("openMenu", js_content)
        self.assertIn("closeMenu", js_content)
        self.assertIn("toggleMenu", js_content)
        self.assertIn("addEventListener", js_content)

    def test_guitar_page_mobile_optimized(self):
        """Test that guitar page is mobile-optimized"""
        with open("apps/guitar/templates/guitar/guitar.html", "r") as f:
            content = f.read()

        # Check for mobile-optimized elements
        self.assertIn("practice-controls", content)
        self.assertIn("chord-selector", content)
        self.assertIn("guitar-neck", content)

    def test_progress_page_mobile_optimized(self):
        """Test that progress page is mobile-optimized"""
        with open("apps/progress/templates/progress/progress.html", "r") as f:
            content = f.read()

        # Check for mobile-optimized elements
        self.assertIn("stats-grid", content)
        self.assertIn("goal-card", content)
        self.assertIn("progress-bar", content)

    def test_navigation_active_state(self):
        """Test that navigation can highlight active page"""
        with open("static/js/navigation.js", "r") as f:
            js_content = f.read()

        # Check for active state handling
        self.assertIn("highlightActivePage", js_content)
        self.assertIn("classList.add('active')", js_content)

    def test_keyboard_navigation(self):
        """Test that navigation supports keyboard interaction"""
        with open("static/js/navigation.js", "r") as f:
            js_content = f.read()

        # Check for ESC key handler
        self.assertIn("e.key === 'Escape'", js_content)

    def test_responsive_images(self):
        """Test that images and media are responsive"""
        with open("static/css/guitar.css", "r") as f:
            css_content = f.read()

        # Check for responsive canvas sizing
        self.assertIn("width: 100%", css_content)
        self.assertIn("max-width", css_content)


class MobileUIIntegrationTestCase(TestCase):
    """Integration tests for mobile UI"""

    def setUp(self):
        """Set up test client and user"""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_full_page_load_mobile(self):
        """Test that mobile-optimized CSS exists"""
        import os

        css_files = [
            "static/css/styles.css",
            "static/css/guitar.css",
            "static/css/progress.css",
        ]

        for css_file in css_files:
            self.assertTrue(os.path.exists(css_file), f"{css_file} does not exist")
            with open(css_file, "r") as f:
                content = f.read()
            # Check for mobile breakpoint
            self.assertIn(
                "@media", content, f"{css_file} missing responsive breakpoints"
            )

    def test_navigation_on_all_authenticated_pages(self):
        """Test that navigation is in base template for authenticated users"""
        with open("apps/core/templates/core/base.html", "r") as f:
            content = f.read()

        # Check for conditional navigation display
        self.assertIn("{% if user.is_authenticated %}", content)
        self.assertIn("navbar", content)

    def test_no_navigation_on_login_page(self):
        """Test that navigation is conditional on authentication"""
        with open("apps/core/templates/core/base.html", "r") as f:
            content = f.read()

        # Navigation should only show for authenticated users
        self.assertIn("{% if user.is_authenticated %}", content)
        self.assertIn("navbar", content)
