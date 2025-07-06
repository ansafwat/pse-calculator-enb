# Android WebView Wrapper Guide

## Quick WebView App Setup

1. **Install Android Studio**
2. **Create a new Android project**
   - Choose "Empty Activity"
   - Name: PSE Calculator Enbridge
   - Package name: com.enbridge.psecalculator

3. **Modify MainActivity.java:**
```java
import android.webkit.WebView;
import android.webkit.WebViewClient;

public class MainActivity extends AppCompatActivity {
    private WebView webView;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        webView = new WebView(this);
        webView.getSettings().setJavaScriptEnabled(true);
        webView.setWebViewClient(new WebViewClient());
        webView.loadUrl("https://your-deployed-app-url.com");
        
        setContentView(webView);
    }
}
```

4. **Add Internet permission in AndroidManifest.xml:**
```xml
<uses-permission android:name="android.permission.INTERNET" />
```

5. **Build and sign your APK**
6. **Upload to Play Store**