package com.cacasians.servermanager;

import android.content.SharedPreferences;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;

public class SettingsActivity extends AppCompatActivity {
    
    private EditText serverUrlEditText;
    private Button saveButton;
    private SharedPreferences preferences;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_settings);
        
        // Setup toolbar
        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        getSupportActionBar().setDisplayHomeAsUpEnabled(true);
        getSupportActionBar().setTitle("Settings");
        
        // Initialize preferences
        preferences = getSharedPreferences("ServerSettings", MODE_PRIVATE);
        
        // Initialize views
        serverUrlEditText = findViewById(R.id.server_url_edit_text);
        saveButton = findViewById(R.id.save_button);
        
        // Load current server URL
        String currentUrl = preferences.getString("server_url", "http://192.168.1.100:5000");
        serverUrlEditText.setText(currentUrl);
        
        // Setup save button
        saveButton.setOnClickListener(v -> saveSettings());
    }
    
    private void saveSettings() {
        String serverUrl = serverUrlEditText.getText().toString().trim();
        
        if (serverUrl.isEmpty()) {
            Toast.makeText(this, "Please enter a server URL", Toast.LENGTH_SHORT).show();
            return;
        }
        
        // Add http:// if not present
        if (!serverUrl.startsWith("http://") && !serverUrl.startsWith("https://")) {
            serverUrl = "http://" + serverUrl;
        }
        
        // Save to preferences
        SharedPreferences.Editor editor = preferences.edit();
        editor.putString("server_url", serverUrl);
        editor.apply();
        
        Toast.makeText(this, "Settings saved successfully", Toast.LENGTH_SHORT).show();
        finish();
    }
    
    @Override
    public boolean onSupportNavigateUp() {
        onBackPressed();
        return true;
    }
}