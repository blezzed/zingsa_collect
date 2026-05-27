const fs = require('fs');

try {
    let content = fs.readFileSync('full.json', 'utf8');
    
    // Append module exports to make it a Node module
    content += "\nmodule.exports = formDefinitions;";
    
    fs.writeFileSync('temp_full.js', content, 'utf8');
    
    const forms = require('./temp_full.js');
    
    fs.writeFileSync('full_clean.json', JSON.stringify(forms, null, 2), 'utf8');
    
    fs.unlinkSync('temp_full.js');
    console.log("SUCCESS");
} catch (error) {
    console.error("ERROR: " + error.message);
    process.exit(1);
}
