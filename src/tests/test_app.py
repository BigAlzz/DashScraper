import sys
from pathlib import Path
import unittest
from dash import Dash, html
import dash

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

class TestDashboardApp(unittest.TestCase):
    def setUp(self):
        self.app = Dash(__name__, use_pages=True, pages_folder=str(src_dir / 'pages'))
        
        # Import pages after app initialization
        import pages.home
        import pages.applications
        import pages.renewals

    def test_home_page_is_default(self):
        """Test that the home page is the default landing page"""
        # Get the registered pages
        pages = dash.page_registry.values()
        
        # Print all registered pages and their configurations for debugging
        print("\nRegistered pages:")
        for page in pages:
            print(f"Path: {page['path']}, Module: {page['module']}, Default: {page.get('default', False)}")
        
        # Verify home page is registered as default
        home_page = next((page for page in pages if page['path'] == '/'), None)
        self.assertIsNotNone(home_page, "Home page not found in registry")
        self.assertTrue(home_page.get('default', False), "Home page not set as default")
        
        # Verify other pages are not set as default
        other_pages = [page for page in pages if page['path'] != '/']
        for page in other_pages:
            self.assertFalse(page.get('default', False), 
                           f"Page {page['path']} should not be set as default")

    def test_page_links(self):
        """Test that all page links are using relative paths"""
        from pages import applications, renewals
        
        def find_back_link(layout):
            """Helper function to find back link in layout"""
            for child in layout.children:
                if isinstance(child, html.Div):
                    for subchild in child.children:
                        if isinstance(subchild, html.A) and subchild.href == '/':
                            return subchild
            return None
        
        # Check applications dashboard back link
        back_link = find_back_link(applications.layout)
        self.assertIsNotNone(back_link, "Back link not found in applications dashboard")
        self.assertEqual(back_link.href, '/', "Applications dashboard back link should use relative path")
        
        # Check renewals dashboard back link
        back_link = find_back_link(renewals.layout)
        self.assertIsNotNone(back_link, "Back link not found in renewals dashboard")
        self.assertEqual(back_link.href, '/', "Renewals dashboard back link should use relative path")

if __name__ == '__main__':
    unittest.main() 