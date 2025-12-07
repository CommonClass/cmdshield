#!/usr/bin/env python3
"""
cmdshield - A Batch File Obfuscator 
Author: commonclass (little bit of gpt help)
Description: This script processes Windows batch files (.bat) to obfuscate variable names,
strings, characters and ints to increase code privacy and deter reverse engineering.  
It renames variables, masks characters, and reconstructs strings using variable references.
Usage: python cmdshield.py <filename.bat>
"""

import re
import os
import sys
import random
from collections import OrderedDict

RANDOM_NAME_LENGTH = 12

BATCH_KEYWORDS = {
    "echo", "if", "else", "for", "in", "do", "exit", "set",
    "setlocal", "endlocal", "goto", "call", "rem", "pause",
    "shift", "cd", "pushd", "popd", "enableextensions",
    "disabledelayedexpansion", "enabledelayedexpansion"
}

#generated regex with gpt :P
SET_REGEX = re.compile(r'^\s*(?:set)\s+([^= \t]+)=(.*)$', re.IGNORECASE)

FOR_LOOP_REGEX = re.compile(
    r'\b(for\s+/L\s+%%[A-Za-z]\s+in\s*\([^)]+\)\s+do\b)',
    re.IGNORECASE
)
FOR_PARAMS_REGEX = re.compile(r'\(([^,]+),([^,]+),([^)]+)\)')
VAR_REF_REGEX = re.compile(r'%([^%]+)%')
DELAYED_VAR_REGEX = re.compile(r'!([^!]+)!')
LOOP_VAR_REGEX = re.compile(r'%%[A-Za-z]')
TOKEN_SPLIT_REGEX = re.compile(
    r'(".*?"|\'.*?\'|%[^%]+%|![^!]+!|%%[A-Za-z]|[^\s]+)'
)

def create_random_name(length=None):
    if length is None:
        length = RANDOM_NAME_LENGTH
    letters = 'abcdefghijklmnopqrstuvwxyz'
    return ''.join(random.choice(letters) for _ in range(length))

def is_keyword(word):
    return word.lower() in BATCH_KEYWORDS

def is_loop_variable(token):
    return bool(LOOP_VAR_REGEX.fullmatch(token))

def is_variable_reference(token):
    return bool(VAR_REF_REGEX.fullmatch(token)) or bool(DELAYED_VAR_REGEX.fullmatch(token))

def split_tokens(line):
    return [token for token in TOKEN_SPLIT_REGEX.findall(line) if token != ""]

def create_math_expression(target_value):
    try:
        target_num = int(target_value)
    except (ValueError, TypeError):
        return str(target_value)
    

    method = random.choice([1, 2, 3])
    
    #basic int math calculation method
    if method == 1:
        a = random.randint(100, 9999)
        b = random.randint(100, 9999)
        result = f"({a} + {b}) - ({a} + {b} - {target_num})"
        
    elif method == 2:
        factor1 = random.randint(5, 50)
        factor2 = random.randint(5, 50)
        product = factor1 * factor2
        result = f"({factor1} * {factor2}) - ({product} - {target_num})"
        
    else:
        base = random.randint(5000, 20000)
        multiplier = random.randint(2, 5)
        total = base * multiplier
        subtract1 = random.randint(1000, 5000)
        subtract2 = total - target_num - subtract1
        result = f"(({base} * {multiplier}) - {subtract1}) - {subtract2}"
    
    return result

def process_batch_file(filepath):
    if not os.path.isfile(filepath):
        print(f"Could not find file: {filepath}")
        return

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
        original_content = infile.read()
    
    original_lines = original_content.splitlines()

    rename_map = {}
    
    for line in original_lines:
        set_match = SET_REGEX.match(line)
        if set_match:
            var_name = set_match.group(1).strip()
            if not is_keyword(var_name) and not is_loop_variable(var_name):
                if var_name not in rename_map:
                    rename_map[var_name] = create_random_name()

    string_replacements = OrderedDict()
    char_replacements = OrderedDict()
    all_chars_found = set()
    
    for line in original_lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()
        
        if not line_stripped or line_stripped.startswith('::'):
            continue
        if line_stripped.startswith('rem '):
            continue

        if line_lower.startswith("echo ") or line_lower.startswith("echo."):
            if line_stripped.lower() == "echo off":
                continue

            echo_match = re.match(r'^\s*echo\s+(.+)$', line, re.IGNORECASE)
            if echo_match:
                echo_text = echo_match.group(1)

                text_no_vars = re.sub(r'%[^%]+%', ' ', echo_text)
                text_no_vars = re.sub(r'![^!]+!', ' ', text_no_vars)

                words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9]*\b', text_no_vars)
                for word in words:
                    if word:
                        string_replacements[word] = "s_" + create_random_name(8)
                for char in text_no_vars:
                    if char.isalpha() or char.isdigit() or char in ' .!?,;:-_':
                        all_chars_found.add(char)

        elif line_lower.startswith("if "):
            quoted_strings = re.findall(r'"([^"]*)"', line)
            for qstring in quoted_strings:
                if qstring:
                    string_replacements[qstring] = "str_" + create_random_name(8)
                for char in qstring:
                    all_chars_found.add(char)
    
    for char in all_chars_found:
        if char not in char_replacements:
            char_replacements[char] = "ch_" + create_random_name(6)
    processed_lines = []
    
    for line_num, current_line in enumerate(original_lines):
        current_line = current_line.rstrip("\n")
        stripped_line = current_line.lstrip()
        line_lower = stripped_line.lower()

        if stripped_line.lower() == "@echo off":
            continue
        
        # for loops obf
        for_loop_match = FOR_LOOP_REGEX.search(current_line)
        if for_loop_match:
            params_match = FOR_PARAMS_REGEX.search(current_line[for_loop_match.start():])
            if params_match:
                start_val = params_match.group(1).strip()
                step_val = params_match.group(2).strip()
                end_val = params_match.group(3).strip()
                indent = current_line[:len(current_line) - len(stripped_line)]
                loop_prefix = "loop" + create_random_name(4)
                start_var = loop_prefix + "_start"
                step_var = loop_prefix + "_step"
                end_var = loop_prefix + "_end"
                start_expr = create_math_expression(start_val)
                step_expr = create_math_expression(step_val)
                end_expr = create_math_expression(end_val)
                processed_lines.append(f"{indent}set /a {start_var}={start_expr}")
                processed_lines.append(f"{indent}set /a {step_var}={step_expr}")
                processed_lines.append(f"{indent}set /a {end_var}={end_expr}")
                loop_var_match = re.search(r'%%([A-Za-z])', current_line)
                loop_var_char = loop_var_match.group(1) if loop_var_match else "i"
                
                new_for_line = f"{indent}for /L %%{loop_var_char} in (!{start_var}!, !{step_var}!, !{end_var}!) do ("
                processed_lines.append(new_for_line)
                
                continue
        
        # sets
        set_match = SET_REGEX.match(current_line)
        if set_match:
            left_side = set_match.group(1).strip()
            right_side = set_match.group(2)
            
            new_left = rename_map.get(left_side, left_side)
            right_stripped = right_side.strip()
            if right_stripped in string_replacements:
                continue
            else:
                processed_lines.append(f"set {new_left}={right_stripped}")
            
            continue
        
        if line_lower.startswith("echo ") or line_lower.startswith("echo."):
            if stripped_line.strip().lower() == "echo off":
                continue
                
            indent = current_line[:len(current_line) - len(stripped_line)]
            echo_parts = line_lower.split(None, 1)
            if len(echo_parts) > 1:
                echo_text = current_line[len(indent) + 4:].lstrip()
            else:
                echo_text = ""
            rebuilt_text = []
            pos = 0
            
            while pos < len(echo_text):
                if echo_text[pos] == '%':
                    end_pos = echo_text.find('%', pos + 1)
                    if end_pos != -1:
                        var_ref = echo_text[pos:end_pos + 1]
                        var_name = var_ref[1:-1]
                        new_var_name = rename_map.get(var_name, var_name)
                        rebuilt_text.append(f"%{new_var_name}%")
                        pos = end_pos + 1
                        continue
                current_char = echo_text[pos]
                if current_char in char_replacements:
                    rebuilt_text.append(f"%{char_replacements[current_char]}%")
                else:
                    rebuilt_text.append(current_char)
                
                pos += 1
            
            new_echo_text = ''.join(rebuilt_text)
            processed_lines.append(f"{indent}echo {new_echo_text}")
            continue

        if line_lower.startswith("if "):
            indent = current_line[:len(current_line) - len(stripped_line)]
            if_content = current_line[len(indent):]
            
            rebuilt_if = []
            pos = 0
            
            while pos < len(if_content):
                if if_content[pos] == '%':
                    end_pos = if_content.find('%', pos + 1)
                    if end_pos != -1:
                        var_ref = if_content[pos:end_pos + 1]
                        var_name = var_ref[1:-1]
                        new_var_name = rename_map.get(var_name, var_name)
                        rebuilt_if.append(f"%{new_var_name}%")
                        pos = end_pos + 1
                        continue
                if if_content[pos] == '"':
                    end_pos = if_content.find('"', pos + 1)
                    if end_pos != -1:
                        quoted_text = if_content[pos + 1:end_pos]    
                        new_quoted = '"'
                        for char in quoted_text:
                            if char in char_replacements:
                                new_quoted += f"%{char_replacements[char]}%"
                            else:
                                new_quoted += char
                        new_quoted += '"'
                        rebuilt_if.append(new_quoted)
                        pos = end_pos + 1
                        continue

                rebuilt_if.append(if_content[pos])
                pos += 1
            
            processed_lines.append(f"{indent}{''.join(rebuilt_if)}")
            continue

        processed_lines.append(current_line)
    
    filename_base, file_extension = os.path.splitext(filepath)
    output_filename = filename_base + "_processed" + file_extension
    
    header_lines = []
    header_lines.append("@echo off")
    header_lines.append("setlocal enabledelayedexpansion")
    header_lines.append("\n:: -=- obfuscated with cmdshield -=- ::\n")
    
    if char_replacements:
        char_init_commands = []
        for char, var_name in char_replacements.items():
            safe_char = char.replace("%", "%%")
            char_init_commands.append(f"set {var_name}={safe_char}")
        
        header_lines.append("&& ".join(char_init_commands))
        header_lines.append("")
    
    for string, str_var in string_replacements.items():
        char_parts = []
        for char in string:
            if char in char_replacements:
                char_parts.append(f"%{char_replacements[char]}%")
            else:
                char_parts.append(char)
        
        if char_parts:
            header_lines.append(f"set {str_var}={''.join(char_parts)}")
    
    header_lines.append("")
    
    for original_var, new_name in rename_map.items():
        original_value = None
        for line in original_lines:
            set_match = SET_REGEX.match(line)
            if set_match and set_match.group(1).strip() == original_var:
                original_value = set_match.group(2).strip()
                break
        
        if original_value:
            if original_value in string_replacements:
                header_lines.append(f"set {new_name}=%{string_replacements[original_value]}%")
            else:
                header_lines.append(f"set {new_name}={original_value}")
    
    header_lines.append("")

    with open(output_filename, 'w', encoding='utf-8') as outfile:
        for line in header_lines:
            outfile.write(line + "\n")

        for line in processed_lines:
            outfile.write(line + "\n")

    print(f"Output saved to: {output_filename}")
    print()
    print(f"Variables renamed: {len(rename_map)}")
    print(f"Characters masked: {len(char_replacements)}")
    print(f"Strings obfuscated: {len(string_replacements)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
    
    input_file = sys.argv[1]
    process_batch_file(input_file)