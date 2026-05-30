/** Simple markdown to HTML converter for security reports. */

export function mdToHtml(md: string): string {
  let html = md
    // Escape HTML entities
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    // Headers
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Inline code
    .replace(/`(.+?)`/g, '<code>$1</code>')
    // Horizontal rules
    .replace(/^---$/gm, '<hr />')
    // Unordered lists
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    // Ordered lists
    .replace(/^\d+\. (.+)$/gm, '<li class="ordered">$1</li>')
    // Blockquotes
    .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
    // Tables (simple)
    .replace(/\|(.+)\|/g, (match) => {
      if (match.includes('---')) return '';
      const cells = match.split('|').filter(c => c.trim()).map(c => `<td>${c.trim()}</td>`).join('');
      return `<tr>${cells}</tr>`;
    })
    // Links
    .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    // Line breaks
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br />');

  // Wrap consecutive list items
  html = html.replace(/((?:<li>.*?<br \/>)+)/g, '<ul>$1</ul>');
  html = html.replace(/<\/ul>\s*<ul>/g, '');
  html = html.replace(/((?:<li class="ordered">.*?<br \/>)+)/g, '<ol>$1</ol>');
  html = html.replace(/<\/ol>\s*<ol>/g, '');

  // Wrap blockquotes
  html = html.replace(/((?:<blockquote>.*?<br \/>)+)/g, '<blockquote>$1</blockquote>');
  html = html.replace(/<\/blockquote>\s*<blockquote>/g, '');

  return `<p>${html}</p>`;
}
