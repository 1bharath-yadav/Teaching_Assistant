#!/usr/bin/env python3
"""
Comparison test showing discourse content before and after optimization.
"""

from data.optimized_chunker import OptimizedChunker
import html2text

def compare_cleaning_methods():
    """Compare basic vs optimized discourse content cleaning."""
    
    # Sample noisy discourse content
    noisy_content = """
    <div class="post">
        <div class="user-info">
            <img src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=" alt="Profile pic">
            <span class="username">@john_doe</span>
            <span class="timestamp">Jan 15, 2024 10:30 AM</span>
        </div>
        
        <div class="post-content">
            <p>This is a really helpful explanation of neural networks!</p>
            
            <blockquote>
                <p>Reply to @previous_user:</p>
                <p>Can someone explain backpropagation?</p>
            </blockquote>
            
            <p>Backpropagation works by calculating gradients:</p>
            <ol>
                <li>Forward pass through the network</li>
                <li>Calculate loss function</li>
                <li>Backward pass to compute gradients</li>
                <li>Update weights using optimizer</li>
            </ol>
            
            <pre><code class="language-python">
import torch
import torch.nn as nn

model = nn.Linear(10, 1)
loss_fn = nn.MSELoss()
optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

# Training step
output = model(input_data)
loss = loss_fn(output, target)
loss.backward()
optimizer.step()
            </code></pre>
            
            <p>For more details, check: <a href="https://pytorch.org/tutorials/beginner/blitz/neural_networks_tutorial.html">PyTorch Neural Networks Tutorial</a></p>
            
            <div class="attachments">
                <img src="https://example.com/diagram.png" alt="Neural network diagram">
                <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" alt="Another embedded image">
            </div>
        </div>
        
        <div class="post-footer">
            <span class="stats">15 views • 3 likes • 2 replies</span>
            <div class="actions">
                <button>Like</button>
                <button>Reply</button>
                <button>Share</button>
                <button>Bookmark</button>
            </div>
        </div>
        
        <div class="meta">
            <p>Post #47 in topic: Neural Networks Discussion</p>
            <p>Category: Deep Learning > Fundamentals</p>
            <p>Tags: neural-networks, backpropagation, pytorch</p>
        </div>
    </div>
    
    <script>
        // Analytics tracking
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', 'GA_TRACKING_ID');
        
        // Discourse specific JS
        console.log("Loading discourse widgets...");
        window.discourse = {
            "user_id": 12345,
            "topic_id": 678,
            "post_id": 47
        };
    </script>
    
    <div class="navigation">
        <a href="/categories">Categories</a>
        <a href="/latest">Latest</a>
        <a href="/top">Top</a>
        <a href="/search">Search</a>
    </div>
    
    {"error": "Failed to load user preferences", "code": 500, "timestamp": "2024-01-15T10:30:00.000Z"}
    
    HTTP/1.1 200 OK
    Content-Type: text/html; charset=utf-8
    Set-Cookie: _discourse_session=abc123; path=/; HttpOnly
    X-Request-Id: chatcmpl-7vFzX8rN2pK9qL3mH6tC4wE1sA9nD
    
    <style>
        .post { margin: 20px; padding: 15px; }
        .hidden { display: none; }
        @media (max-width: 768px) { .post { margin: 10px; } }
    </style>
    """
    
    print("📊 Discourse Content Cleaning Comparison")
    print("=" * 80)
    
    # Method 1: Basic html2text only
    h2t = html2text.HTML2Text()
    h2t.ignore_links = False  # Keep links for comparison
    h2t.ignore_images = True
    
    basic_cleaned = h2t.handle(noisy_content)
    
    print(f"🔧 Method 1: Basic html2text cleaning")
    print(f"   Length: {len(basic_cleaned)} characters")
    print(f"   Preview: {basic_cleaned[:200]}...")
    
    # Method 2: Optimized cleaning pipeline
    chunker = OptimizedChunker()
    
    # Step-by-step optimization
    step1 = chunker.clean_html_content(noisy_content)
    step2 = chunker._clean_discourse_specific_content(step1)
    
    print(f"\n🚀 Method 2: Optimized cleaning pipeline")
    print(f"   After HTML cleaning: {len(step1)} characters")
    print(f"   After discourse cleaning: {len(step2)} characters")
    print(f"   Final preview: {step2[:300]}...")
    
    # Analysis
    reduction_basic = len(noisy_content) - len(basic_cleaned)
    reduction_optimized = len(noisy_content) - len(step2)
    
    print(f"\n📈 Cleaning Effectiveness Comparison:")
    print(f"   Original content: {len(noisy_content)} characters")
    print(f"   Basic cleaning: {len(basic_cleaned)} chars (removed {reduction_basic}, {reduction_basic/len(noisy_content)*100:.1f}%)")
    print(f"   Optimized cleaning: {len(step2)} chars (removed {reduction_optimized}, {reduction_optimized/len(noisy_content)*100:.1f}%)")
    print(f"   Additional optimization: {len(basic_cleaned) - len(step2)} chars ({(len(basic_cleaned) - len(step2))/len(basic_cleaned)*100:.1f}% better)")
    
    # Quality check
    print(f"\n🔍 Content Quality Analysis:")
    
    def check_quality(content, label):
        issues = []
        if 'data:image' in content:
            issues.append("❌ Base64 images")
        if any(x in content for x in ['HTTP/', 'Content-Type:', 'Set-Cookie:']):
            issues.append("❌ HTTP headers")
        if any(x in content for x in ['console.log', 'window.', 'gtag(']):
            issues.append("❌ JavaScript code")
        if any(x in content for x in ['"error":', '"code":', 'chatcmpl-']):
            issues.append("❌ JSON errors/API responses")
        if any(x in content for x in ['views •', 'likes •', 'Post #']):
            issues.append("❌ UI metadata")
        if '@' in content and any(x in content for x in ['Reply to', 'mentioned']):
            issues.append("❌ User mentions")
        
        clean_indicators = []
        if any(x in content for x in ['import torch', 'nn.Linear', 'loss.backward()']):
            clean_indicators.append("✅ Code examples")
        if 'PyTorch' in content or 'Neural Networks' in content:
            clean_indicators.append("✅ Educational content")
        if 'https://' in content and 'pytorch.org' in content:
            clean_indicators.append("✅ Meaningful links")
        if any(x in content for x in ['Forward pass', 'gradients', 'optimizer']):
            clean_indicators.append("✅ Technical explanations")
        
        print(f"   {label}:")
        for issue in issues:
            print(f"     {issue}")
        for indicator in clean_indicators:
            print(f"     {indicator}")
        if not issues:
            print(f"     ✅ Clean content!")
        print()
    
    check_quality(basic_cleaned, "Basic cleaning")
    check_quality(step2, "Optimized cleaning")
    
    print("🎯 Optimization Benefits:")
    print("   📚 Preserves educational content and code examples")
    print("   🔗 Keeps meaningful documentation links")
    print("   🗑️  Removes UI clutter and technical noise")
    print("   🧹 Eliminates base64 images and API responses")
    print("   ⚡ Better content quality for embeddings")
    print("   🎯 Forum-specific pattern removal")

if __name__ == "__main__":
    compare_cleaning_methods()
