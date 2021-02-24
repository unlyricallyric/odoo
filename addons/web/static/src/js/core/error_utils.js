/** @odoo-module **/

import { loadJS } from "web.ajax";
import BrowserDetection from "web.BrowserDetection";
/**
 * Format the traceback of an error.  Basically, we just add the error message
 * in the traceback if necessary (Chrome already does it by default, but not
 * other browser. yay for non standard APIs)
 *
 * @param {Error} error 
 * @returns {string}
 */
export function formatTraceback(error) {
  const traceback = error.stack;
  // Error.prototype.stack is non-standard.
  // https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Error
  // However, most engines provide an implementation.
  // In particular, Chrome formats the contents of Error.stack
  // https://v8.dev/docs/stack-trace-api#compatibility
  const browserDetection = new BrowserDetection();
  if (browserDetection.isBrowserChrome()) {
      return error.stack;
  } else {
      return `${_t("Error:")} ${error.message}\n${error.stack}`;
  }
}

/**
* Returns an annotated traceback from an error. This is asynchronous because
* it needs to fetch the sourcemaps for each script involved in the error,
* then compute the correct file/line numbers and add the information to the
* correct line.
* 
* @param {Error} error 
* @returns {Promise<string>}
*/
export async function annotateTraceback(error) {
  const traceback = formatTraceback(error);
  await loadJS('/web/static/lib/stacktracejs/stacktrace.js');
  const frames = await StackTrace.fromError(error);
  const lines = traceback.split('\n');
  if (lines[lines.length-1].trim() === "") {
      // firefox traceback have an empty line at the end
      lines.splice(-1);
  }

  // Chrome stacks contains some lines with (index 0) which apparently
  // corresponds to some native functions (at least Promise.all). We need to
  // ignore them because they will not correspond to a stackframe.
  const skips = lines.filter(l => l.includes("(index 0")).length;
  const offset = lines.length - frames.length - skips;
  let lineIndex = offset;
  let frameIndex = 0;
  while (frameIndex < frames.length) {
      const line = lines[lineIndex];
      if (line.includes("(index 0)")) {
          lineIndex++;
          continue;
      }
      const frame = frames[frameIndex];
      const info = ` (${frame.fileName}:${frame.lineNumber})`;
      lines[lineIndex] = line + info;
      lineIndex++;
      frameIndex++;
  }
  return lines.join('\n');
}
