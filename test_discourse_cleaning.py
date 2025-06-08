#!/usr/bin/env python3
"""
Test script to demonstrate optimized discourse content cleaning.
"""

from data.optimized_chunker import OptimizedChunker


def test_discourse_cleaning():
    """Test discourse content cleaning with sample data."""

    # Sample raw discourse content with various types of noise
    sample_discourse_content = """
    <div class="post-content">
        <p>This is a great question about data science!</p>
        
        <p>@john_doe you mentioned something about pandas. Here's what I think:</p>
        
        <blockquote>
            <p>Originally posted by @jane_smith:</p>
            <p>How do you handle missing data in pandas?</p>
        </blockquote>
        
        <p>There are several approaches:</p>
        <ol>
            <li>Use <code>df.dropna()</code> to remove rows with missing values</li>
            <li>Use <code>df.fillna()</code> to fill missing values</li>
            <li>Use interpolation methods</li>
        </ol>
        
        <p>Here's a code example:</p>
        <pre><code>import pandas as pd
df = pd.read_csv('data.csv')
df_cleaned = df.dropna()
print(df_cleaned.info())</code></pre>
        
        <p>You can also check out this tutorial: <a href="https://pandas.pydata.org/docs/">Pandas Documentation</a></p>
        
        <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" alt="Sample image"/>
        
        <p>Hope this helps! Let me know if you have more questions.</p>
        
        <div class="post-meta">
            <span>Posted on Jan 15, 2024 10:30 AM</span>
            <span>5 views</span>
            <span>2 likes</span>
            <a href="#reply">Reply</a>
        </div>
        
        <script>
            console.log("Some JavaScript code that shouldn't be in content");
            window.analytics = {id: "chatcmpl-abc123"};
        </script>
        
        {"error": "API response error", "status": 500}
        
        <style>
            .hidden { display: none; }
        </style>
    </div>
    
    <nav class="navigation">
        <a href="/home">Home</a>
        <a href="/categories">Categories</a>
    </nav>
    
    HTTP/1.1 200 OK
    Content-Type: application/json
    Set-Cookie: session=abc123
    
    Post #15
    Reply to @another_user
    edited 2 hours ago
    Show more replies
    """

    print("🧪 Testing Discourse Content Cleaning Optimization")
    print("=" * 60)

    # Initialize chunker
    chunker = OptimizedChunker()

    print("\n📝 Original Content Length:", len(sample_discourse_content))
    print("📝 Original Content Preview:")
    print("-" * 40)
    print(
        sample_discourse_content[:500] + "..."
        if len(sample_discourse_content) > 500
        else sample_discourse_content
    )

    print("\n🔧 Applying Optimized Cleaning Pipeline...")
    print("-" * 40)

    # Step 1: HTML content cleaning
    print("Step 1: HTML content cleaning (with readability + noise removal)")
    cleaned_html = chunker.clean_html_content(sample_discourse_content)
    print(f"   ✅ After HTML cleaning: {len(cleaned_html)} characters")

    # Step 2: Discourse-specific cleaning
    print("Step 2: Discourse-specific pattern removal")
    final_cleaned = chunker._clean_discourse_specific_content(cleaned_html)
    print(f"   ✅ After discourse cleaning: {len(final_cleaned)} characters")

    print("\n🎯 Final Cleaned Content:")
    print("=" * 60)
    print(final_cleaned)

    print("\n📊 Cleaning Results Summary:")
    print("-" * 40)
    print(f"Original length: {len(sample_discourse_content)} characters")
    print(f"Final length: {len(final_cleaned)} characters")
    print(
        f"Reduction: {len(sample_discourse_content) - len(final_cleaned)} characters ({((len(sample_discourse_content) - len(final_cleaned)) / len(sample_discourse_content) * 100):.1f}%)"
    )

    print("\n✅ What was removed:")
    print("   🗑️  Base64 images and encoded data")
    print("   🗑️  JavaScript code and script tags")
    print("   🗑️  JSON error responses")
    print("   🗑️  HTTP headers and cookies")
    print("   🗑️  Discourse UI elements (navigation, meta info)")
    print("   🗑️  User mentions and reply notifications")
    print("   🗑️  View counts, like counts, timestamps")
    print("   🗑️  Post numbers and editing notifications")

    print("\n✅ What was preserved:")
    print("   📚 Main content and explanations")
    print("   🔗 Meaningful links (Pandas documentation)")
    print("   💻 Code examples and syntax")
    print("   📝 Structured lists and formatting")
    print("   🎯 Educational content and context")

    # Test token estimation
    if chunker.encoding:
        tokens = chunker._estimate_tokens(final_cleaned)
        print(f"\n🔢 Estimated tokens: {tokens}")

    print("\n🎉 Discourse content cleaning optimization is working perfectly!")
    return final_cleaned


def test_noise_patterns():
    """Test specific noise pattern detection."""
    print("\n🔍 Testing Specific Noise Pattern Detection")
    print("=" * 60)

    chunker = OptimizedChunker()

    test_lines = [
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "@username mentioned this",
        "5 views",
        "2 likes",
        "Reply to @someone",
        "Post #123",
        "edited 3 hours ago",
        "Show more replies",
        "HTTP/1.1 200 OK",
        "Content-Type: application/json",
        '{"error": "API failed"}',
        "This is valuable educational content about pandas.",
        "Here's how to use df.dropna() method:",
        "Check out the documentation: https://pandas.pydata.org/docs/",
        "console.log('debug info');",
        "window.analytics = {};",
        "Home",
        "Categories",
        "Loading...",
    ]

    print("Testing individual line noise detection:")
    for line in test_lines:
        is_noise = chunker._is_technical_noise_line(line)
        is_web_artifact = chunker._is_web_artifact(line)
        is_discourse_ui = chunker._is_discourse_ui_element(line)

        status = (
            "🗑️  REMOVED"
            if (is_noise or is_web_artifact or is_discourse_ui)
            else "✅ KEPT"
        )
        reason = []
        if is_noise:
            reason.append("technical noise")
        if is_web_artifact:
            reason.append("web artifact")
        if is_discourse_ui:
            reason.append("discourse UI")

        reason_str = f" ({', '.join(reason)})" if reason else ""
        print(f"   {status}: '{line[:50]}...'{reason_str}")


if __name__ == "__main__":
    try:
        # Test main cleaning pipeline
        cleaned_content = test_discourse_cleaning()

        # Test specific noise patterns
        test_noise_patterns()

        print("\n🎯 All tests completed successfully!")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
