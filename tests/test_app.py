import unittest
import os

os.environ['TESTING'] = 'true'

from app import app, mydb, TimelinePost

class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        
    def test_home(self):
        response = self.client.get('/', follow_redirects=True)
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert '<title>MLH Fellow</title>' in html

        # Test home page redirects to portfolio
        response = self.client.get('/')
        assert response.status_code == 302
        assert '/portfolio' in response.location

    def test_timeline(self):
        response = self.client.get('/api/timeline_post')
        assert response.status_code == 200
        assert response.is_json
        json = response.get_json()
        assert "timeline_posts" in json
        assert len(json["timeline_posts"]) == 0

        # Test POST API for timeline posts
        post_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'content': 'This is a test post'
        }
        response = self.client.post('/api/timeline_post', data=post_data)
        assert response.status_code == 200
        assert response.is_json
        json = response.get_json()
        assert json['name'] == 'Test User'
        assert json['email'] == 'test@example.com'
        assert json['content'] == 'This is a test post'
        
        # Verify the post was added by checking GET API
        response = self.client.get('/api/timeline_post')
        json = response.get_json()
        assert len(json["timeline_posts"]) == 1
        assert json["timeline_posts"][0]['name'] == 'Test User'
        
        # Test timeline page rendering
        response = self.client.get('/timeline')
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert '<title>Timeline</title>' in html
        assert 'Test User' in html
        assert 'This is a test post' in html

    def test_malformed_timeline_post(self):
    # POST request missing name
        response = self.client.post("/api/timeline_post", data={
            "email": "john@example.com", "content": "Hello world, I'm John!"
        })
        assert response.status_code == 400
        html = response.get_data(as_text=True)
        assert "Invalid name" in html

        # POST request with empty content
        response = self.client.post("/api/timeline_post", data={
            "name": "John Doe", "email": "john@example.com", "content": ""
        })
        assert response.status_code == 400
        html = response.get_data(as_text=True)
        assert "Invalid content" in html

        # POST request with malformed email
        response = self.client.post("/api/timeline_post", data={
            "name": "John Doe", "email": "not-an-email", "content": "Hello world, I'm John!"
        })
        assert response.status_code == 400
        html = response.get_data(as_text=True)
        assert "Invalid email" in html
