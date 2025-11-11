#!/usr/bin/env python3
"""
Simple web application for studying Argentine history.

This script uses Python's built‑in http.server library to serve a small
website with four static sections and a basic blog. The blog allows
an administrator to add posts via a form; posts are stored in a JSON file
on disk. There is no authentication; anyone with access to the server can
add posts. All HTML templates are stored in the 'templates' directory and
rendered with minimal string substitution.
"""

from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import os
import json
# Import typing for Python versions prior to 3.9
try:
    # Python 3.9+ supports builtin generics on dict/list
    from typing import Dict, Optional, List, Any  # noqa: F401
except ImportError:
    from typing import Dict, Optional, List, Any  # noqa: F401


class HistoryHandler(SimpleHTTPRequestHandler):
    """Custom request handler to serve dynamic and static pages."""

    def _render_template(self, template_name: str, context: Optional[Dict[str, str]] = None) -> bytes:
        """Load an HTML template from the templates directory and return it with
        placeholders replaced according to the context. The templates use
        double curly braces {{key}} for substitution.
        """
        context = context or {}
        template_path = os.path.join(os.path.dirname(__file__), 'templates', template_name)
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Replace placeholders
        for key, value in context.items():
            content = content.replace(f'{{{{{key}}}}}', value)
        return content.encode('utf-8')

    def _load_posts(self) -> List[Dict[str, Any]]:
        """Load posts from the JSON file. If file does not exist or is invalid, return empty list."""
        posts_file = os.path.join(os.path.dirname(__file__), 'posts.json')
        if not os.path.exists(posts_file):
            return []
        try:
            with open(posts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    def _save_posts(self, posts: List[Dict[str, Any]]) -> None:
        """Save posts list to the JSON file."""
        posts_file = os.path.join(os.path.dirname(__file__), 'posts.json')
        with open(posts_file, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)

    def do_GET(self):
        """Handle GET requests for dynamic paths and fall back to static files."""
        path = self.path.split('?', 1)[0]
        if path in ('/', '/section1', '/section2', '/section3', '/blog', '/admin/new_post'):
            if path == '/':
                content = self._render_template('home_static.html', {'title': 'Principal'})
            elif path == '/section1':
                content = self._render_template('section1_static.html', {'title': 'Sección 1'})
            elif path == '/section2':
                content = self._render_template('section2_static.html', {'title': 'Sección 2'})
            elif path == '/section3':
                content = self._render_template('section3_static.html', {'title': 'Sección 3'})
            elif path == '/blog':
                posts = self._load_posts()
                # Sort posts by id descending
                posts_sorted = sorted(posts, key=lambda p: p.get('id', 0), reverse=True)
                posts_html_parts = []
                for post in posts_sorted:
                    title = post.get('title', '')
                    content_text = post.get('content', '')
                    posts_html_parts.append(f'<div class="post"><h2>{title}</h2><p>{content_text}</p></div>')
                posts_html = '\n'.join(posts_html_parts) if posts_html_parts else '<p>No hay posts todavía. ¡Agrega uno nuevo!</p>'
                content = self._render_template('blog_static.html', {'title': 'Blog', 'posts': posts_html})
            else:  # '/admin/new_post'
                content = self._render_template('new_post_static.html', {'title': 'Nuevo Post'})
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content)
        else:
            # Fallback: serve static files (like CSS if needed)
            super().do_GET()

    def do_POST(self):
        """Handle POST requests for adding new blog posts."""
        if self.path == '/admin/new_post':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = parse_qs(post_data)
            title_list = params.get('title', [])
            content_list = params.get('content', [])
            if title_list and content_list:
                title = title_list[0].strip()
                content_text = content_list[0].strip()
                if title and content_text:
                    posts = self._load_posts()
                    next_id = max([p.get('id', 0) for p in posts], default=0) + 1
                    posts.append({'id': next_id, 'title': title, 'content': content_text})
                    self._save_posts(posts)
            # Redirect back to blog after processing
            self.send_response(303)
            self.send_header('Location', '/blog')
            self.end_headers()
        else:
            # Unknown POST; respond with 404
            self.send_response(404)
            self.end_headers()


def run_server(host: str = '0.0.0.0', port: int = 8000) -> None:
    """Run the HTTP server."""
    httpd = HTTPServer((host, port), HistoryHandler)
    print(f"Serving on http://{host}:{port}")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()