export const LANGUAGE_MAP: { [key: string]: string } = {
  'js': 'javascript',
  'mjs': 'javascript',
  'jsx': 'jsx',
  'ts': 'typescript',
  'tsx': 'jsx', // Default for TSX (overridden by special logic)
  'py': 'python',
  'pyw': 'python',
  'java': 'java',
  'c': 'c',
  'cpp': 'cpp',
  'cc': 'cpp',
  'cxx': 'cpp',
  'c++': 'cpp',
  'h': 'c',
  'hpp': 'cpp',
  'hxx': 'cpp',
  'cs': 'csharp',
  'php': 'php',
  'php3': 'php',
  'php4': 'php',
  'php5': 'php',
  'phtml': 'php',
  'rb': 'ruby',
  'ruby': 'ruby',
  'go': 'go',
  'rs': 'rust',
  'swift': 'swift',
  'kt': 'kotlin',
  'kts': 'kotlin',
  'scala': 'scala',
  'sc': 'scala',
  'sh': 'bash',
  'bash': 'bash',
  'zsh': 'bash',
  'fish': 'bash',
  'ps1': 'powershell',
  'psm1': 'powershell',
  'sql': 'sql',
  'mysql': 'sql',
  'pgsql': 'sql',
  'html': 'markup',
  'htm': 'markup',
  'xhtml': 'markup',
  'xml': 'markup',
  'svg': 'markup',
  'css': 'css',
  'scss': 'scss',
  'sass': 'sass',
  'less': 'less',
  'json': 'json',
  'json5': 'json5',
  'jsonc': 'json',
  'yaml': 'yaml',
  'yml': 'yaml',
  'toml': 'toml',
  'ini': 'ini',
  'cfg': 'ini',
  'conf': 'nginx',
  'dockerfile': 'docker',
  'containerfile': 'docker',
  'md': 'markdown',
  'markdown': 'markdown',
  'mdx': 'mdx',
  'tex': 'latex',
  'r': 'r',
  'rmd': 'r',
  'matlab': 'matlab',
  'm': 'objectivec', // Could be Objective-C or MATLAB
  'mm': 'objectivec',
  'pl': 'perl',
  'pm': 'perl',
  'lua': 'lua',
  'vim': 'vim',
  'makefile': 'makefile',
  'mk': 'makefile',
  'cmake': 'cmake',
  'gradle': 'gradle',
  'groovy': 'groovy',
  'clj': 'clojure',
  'cljs': 'clojure',
  'hs': 'haskell',
  'elm': 'elm',
  'dart': 'dart',
  'vue': 'markup', // Vue files are essentially HTML templates
  'svelte': 'markup'
};

export const DEFAULT_LANGUAGE = 'javascript'; 