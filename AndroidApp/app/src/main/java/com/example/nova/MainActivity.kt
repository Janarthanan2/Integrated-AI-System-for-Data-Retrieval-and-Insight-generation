package com.example.nova

import android.content.Context
import android.content.SharedPreferences
import android.os.Bundle
import android.text.InputType
import android.view.Menu
import android.view.MenuItem
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.EditText
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity


class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private val PREFS_NAME = "NovaPrefs"
    private val KEY_SERVER_URL = "server_url"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webview)
        
        val webSettings: WebSettings = webView.settings
        webSettings.javaScriptEnabled = true
        webSettings.domStorageEnabled = true
        
        // Improve performance
        webSettings.cacheMode = WebSettings.LOAD_DEFAULT
        
        // Ensure links open within the WebView, not external browser
        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, url: String?): Boolean {
                view?.loadUrl(url ?: "")
                return true
            }

            override fun onReceivedError(view: WebView?, request: android.webkit.WebResourceRequest?, error: android.webkit.WebResourceError?) {
                super.onReceivedError(view, request, error)
                // Avoid showing alert for standard errors during page load unless it's the main frame
                if (request?.isForMainFrame == true) {
                    showErrorDialog()
                }
            }
        }

        checkAndLoadUrl()
    }

    private fun checkAndLoadUrl() {
        val settings = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val savedUrl = settings.getString(KEY_SERVER_URL, "")

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
            .setPositiveButton("Yes (Auto)") { _, _ ->
                settings.edit().putString(KEY_SERVER_URL, autoUrl).apply()
                loadWebUrl(autoUrl)
            }
            .setNegativeButton("No (Local/Other)") { _, _ ->
                 // Offer Local or Manual
                 showLocalOrManualDialog(settings)
            }
            .setCancelable(false)
            .show()
    }

    private fun showLocalOrManualDialog(settings: SharedPreferences) {
         AlertDialog.Builder(this)
            .setTitle("Local or Manual?")
            .setMessage("Connect to Local WiFi (192.168.0.107) or enter a custom URL?")
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
        input.hint = "https://your-app.ngrok-free.app"

        AlertDialog.Builder(this)
            .setTitle("Enter Remote URL")
            .setMessage("Enter your ngrok URL:")
            .setView(input)
            .setCancelable(false)
            .setPositiveButton("Save") { _, _ ->
                var url = input.text.toString().trim()
                if (url.isNotEmpty()) {
                    if (!url.startsWith("http://") && !url.startsWith("https://")) {
                        url = "http://$url"
                    }
                    settings.edit().putString(KEY_SERVER_URL, url).apply()
                    loadWebUrl(url)
                } else {
                    showUrlDialog(settings)
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
            .setMessage("Could not connect to the server. Check your internet connection or update the Server URL.")
            .setPositiveButton("Change URL") { _, _ ->
                val settings = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
                showConnectionChoiceDialog(settings)
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
                val settings = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
                showConnectionChoiceDialog(settings)
                true
            }
            else -> super.onOptionsItemSelected(item)
        }
    }

    private fun loadWebUrl(url: String) {
        val extraHeaders: MutableMap<String, String> = HashMap()
        extraHeaders["ngrok-skip-browser-warning"] = "true"
        webView.loadUrl(url, extraHeaders)
    }

    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}
