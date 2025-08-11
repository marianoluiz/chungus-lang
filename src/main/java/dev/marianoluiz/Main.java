package dev.marianoluiz;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Main.java
 * ----------
 * Entry point for the Hue language compiler.
 *
 * Responsibilities:
 * - Accepts a source file path as a command-line argument.
 * - Reads the contents of the specified file.
 * - (Planned) Passes the file contents to the lexer for tokenization.
 *
 * Usage:
 * java -jar hue.jar <source-file>
 *
 * Arguments:
 * args[0] : Path to the source file (e.g., program.hue)
 *
 */
public class Main 
{
    public static void main( String[] args )
    {
        if (args.length < 1) {
            System.err.println("""
                               \nUsage
                               jar: java -jar hue.jar <file.hue>
                               class: java -cp target/classes dev.marianoluiz.Main <file.hue>
                               """);
            System.exit(1);
        }
        
        // contains path of <file>.hue
        String filePath = args[0];
        
        try {
            System.out.println("\nReceived File Path: " + filePath);
            Path pathObj = Path.of(filePath);
            String content = Files.readString(pathObj);

            // TODO: lexer

            System.out.println("File Content: " + content);
        } catch (IOException e) {
            System.err.println("Error reading file " + filePath + ": " + e.getMessage());
            System.exit(1);
        }

    }
}