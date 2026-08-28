import "@testing-library/jest-dom";
import "whatwg-fetch";
import { TextDecoder, TextEncoder } from "node:util";
import { ReadableStream } from "node:stream/web";

// jsdom lacks TextEncoder and ReadableStream — required by SSE mock helpers.
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder as typeof global.TextDecoder;
global.ReadableStream = ReadableStream as typeof global.ReadableStream;

// jsdom does not implement scrollTop/scrollHeight — stub for chat scroll tests.
Object.defineProperty(HTMLElement.prototype, "scrollTop", {
  writable: true,
  value: 0,
});
Object.defineProperty(HTMLElement.prototype, "scrollHeight", {
  writable: true,
  value: 0,
});
