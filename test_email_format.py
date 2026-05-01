from tools.email_tool import send_email

html = """
<div style="font-family: sans-serif; padding: 20px; color: #333;">
    <h2>Hello Tanisha! 🚀</h2>
    <p>We noticed you haven't fully set up your job preferences yet.</p>
    <p><strong>Set up your preferences fast to get job updates!</strong></p>
    <p>Once you define your target domains and locations, our AI agents will start searching and mailing you the best opportunities every day.</p>
    <div style="margin-top: 30px;">
        <a href="https://tanishapritha-job-crew.hf.space" style="background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Set Preferences Now</a>
    </div>
</div>
"""

result = send_email('tpritha190304@gmail.com', '🚀 Set up your job preferences!', html)
print(f"Result: {result}")
