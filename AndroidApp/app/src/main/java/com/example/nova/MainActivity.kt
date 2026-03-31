package com.example.nova

import android.content.Context
import android.content.SharedPreferences
import android.graphics.Bitmap
import android.net.http.SslError
import android.os.Bundle
import android.text.InputType
import android.util.Log
import android.view.Menu
import android.view.MenuItem
import android.webkit.*
import android.widget.EditText
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private val PREFS_NAME = "NovaPrefs"
    private val KEY_SERVER_URL = "server_url"
    private val TAG = "NovaWebView"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webview)
        
        // Enable Chrome DevTools debugging (connect phone to PC and go to chrome://inspect)
        WebView.setWebContentsDebuggingEnabled(true)

        // Setup Cookie Manager
        val cookieManager = CookieManager.getInstance()
        cookieManager.setAcceptCookie(true)
        cookieManager.setAcceptThirdPartyCookies(webView, true)

        val webSettings: WebSettings = webView.settings
        webSettings.javaScriptEnabled = true
        webSettings.domStorageEnabled = true
        webSettings.databaseEnabled = true
        webSettings.loadWithOverviewMode = true
        webSettings.useWideViewPort = true
        webSettings.allowFileAccess = true
        webSettings.allowContentAccess = true
        
        // Set a non-standard User Agent to completely bypass the ngrok browser warning page.
        // Ngrok only shows the warning to standard browsers. By using a custom User-Agent,
        // it treats the app as an API client and allows all HTML/JS/CSS through seamlessly.
        webSettings.userAgentString = "NovaApp-Android/1.0"
        
        webSettings.mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
        webSettings.cacheMode = WebSettings.LOAD_DEFAULT
        
        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                val url = request?.url?.toString() ?: ""
                Log.d(TAG, "Navigating to: $url")
                // Inject headers on navigation
                loadWebUrl(url)
                return true
            }

            override fun onPageStarted(view: WebView?, url: String?, favicon: Bitmap?) {
                super.onPageStarted(view, url, favicon)
                Log.d(TAG, "Page started: $url")
            }

            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                Log.d(TAG, "Page finished: $url")
                // Flush cookies to disk
                CookieManager.getInstance().flush()
            }

            override fun onReceivedError(view: WebView?, request: WebResourceRequest?, error: WebResourceError?) {
                super.onReceivedError(view, request, error)
                if (request?.isForMainFrame == true) {
                    Log.e(TAG, "Load Error: ${error?.description}")
                    showErrorDialog()
                }
            }

            override fun onReceivedSslError(view: WebView?, handler: SslErrorHandler?, error: SslError?) {
                Log.w(TAG, "SSL Error bypassed: $error")
                // Proceed with SSL certificate errors (common with tunnels like ngrok)
                handler?.proceed()
            }
        }

        webView.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(view: WebView?, newProgress: Int) {
                Log.d(TAG, "Loading Progress: $newProgress%")
            }

            override fun onConsoleMessage(consoleMessage: ConsoleMessage?): Boolean {
                Log.d(TAG, "JS Console: ${consoleMessage?.message()} [Line ${consoleMessage?.lineNumber()}]")
                return true
            }
        }

        checkAndLoadUrl()
    }

    private fun checkAndLoadUrl() {
        val settings = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val savedUrl = settings.getString(KEY_SERVER_URL, "")
        val autoUrl = "https://lamonica-proalliance-annamae.ngrok-free.dev"
        val lastAutoUrl = settings.getString("last_auto_url", "")

        // If the autoUrl in code changed since last launch, reset the saved URL
        if (autoUrl != lastAutoUrl) {
            settings.edit().putString("last_auto_url", autoUrl).apply()
            settings.edit().putString(KEY_SERVER_URL, autoUrl).apply()
            loadWebUrl(autoUrl)
            return
        }

        if (savedUrl.isNullOrEmpty()) {
            showConnectionChoiceDialog(settings)
        } else {
            loadWebUrl(savedUrl)
        }
    }

    private fun showConnectionChoiceDialog(settings: SharedPreferences) {
        val autoUrl = "https://lamonica-proalliance-annamae.ngrok-free.dev"
        AlertDialog.Builder(this)
            .setTitle("Select Connection")
            .setMessage("Connect to Auto Remote URL?\n\n$autoUrl")
            .setPositiveButton("Yes") { _, _ ->
                settings.edit().putString(KEY_SERVER_URL, autoUrl).apply()
                loadWebUrl(autoUrl)
            }
            .setNegativeButton("Manual/Local") { _, _ ->
                 showLocalOrManualDialog(settings)
            }
            .setCancelable(false)
            .show()
    }

    private fun showLocalOrManualDialog(settings: SharedPreferences) {
         AlertDialog.Builder(this)
            .setTitle("Local or Manual?")
            .setMessage("Choose connection type:")
            .setPositiveButton("Local (WiFi)") { _, _ ->
                val localUrl = "http://192.168.0.107:5173"
                settings.edit().putString(KEY_SERVER_URL, localUrl).apply()
                loadWebUrl(localUrl)
            }
            .setNegativeButton("Manual Input") { _, _ ->
                showUrlDialog(settings)
            }
            .show()
    }

    private fun showUrlDialog(settings: SharedPreferences) {
        val input = EditText(this)
        input.inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_URI
        input.hint = "https://example.ngrok-free.app"

        AlertDialog.Builder(this)
            .setTitle("Enter URL")
            .setView(input)
            .setCancelable(false)
            .setPositiveButton("Save") { _, _ ->
                var url = input.text.toString().trim()
                if (url.isNotEmpty()) {
                    if (!url.startsWith("http://") && !url.startsWith("https://")) {
                        url = "https://$url"
                    }
                    settings.edit().putString(KEY_SERVER_URL, url).apply()
                    loadWebUrl(url)
                }
            }
            .setNegativeButton("Back") { _, _ ->
                showConnectionChoiceDialog(settings)
            }
            .show()
    }

    private fun showErrorDialog() {
        AlertDialog.Builder(this)
            .setTitle("Connection Failed")
            .setMessage("Could not connect to the server.")
            .setPositiveButton("Settings") { _, _ ->
                showConnectionChoiceDialog(getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE))
            }
            .setNegativeButton("Retry") { _, _ ->
                 webView.reload()
            }
            .setCancelable(false)
            .show()
    }

    override fun onCreateOptionsMenu(menu: Menu?): Boolean {
        menuInflater.inflate(R.menu.main_menu, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        return when (item.itemId) {
            R.id.action_reset_url -> {
                showConnectionChoiceDialog(getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE))
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }

    private fun loadWebUrl(url: String) {
        // We load the URL without headers because ngrok needs to set a cookie via standard HTML navigation.
        // Injecting the ngrok-skip-browser-warning header bypasses the cookie, which blocks subsequent JS/CSS asset requests.
        webView.loadUrl(url)
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}
