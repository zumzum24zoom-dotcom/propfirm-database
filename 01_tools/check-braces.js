const fs = require('fs');
const src = fs.readFileSync('01_tools/page-maker-v11.html', 'utf8');
const lines = src.split('\n');
const vtContent = lines.slice(857, 1367).join('\n');
const vtLines = vtContent.split('\n');

let opens = 0, closes = 0;
let i = 0;

function skipString(q) {
  i++; // skip opening quote
  while (i < vtContent.length) {
    if (vtContent[i] === '\\') { i += 2; continue; }
    if (vtContent[i] === q) { i++; return; }
    i++;
  }
}

function countInExpr() {
  // We're inside ${...}, count braces properly
  let d = 1;
  while (i < vtContent.length && d > 0) {
    const c = vtContent[i];
    if (c === '{') { opens++; d++; i++; }
    else if (c === '}') { closes++; d--; i++; }
    else if (c === '`') { skipTemplate(); }
    else if (c === '"') { skipString('"'); }
    else if (c === "'") { skipString("'"); }
    else { i++; }
  }
}

function skipTemplate() {
  i++; // skip opening backtick
  while (i < vtContent.length) {
    const c = vtContent[i];
    if (c === '\\') { i += 2; continue; }
    if (c === '`') { i++; return; }
    if (c === '$' && vtContent[i+1] === '{') {
      opens++; i += 2; // count the { and skip ${
      countInExpr();
      continue;
    }
    i++;
  }
}

while (i < vtContent.length) {
  const c = vtContent[i];
  if (c === '`') { skipTemplate(); }
  else if (c === '"') { skipString('"'); }
  else if (c === "'") { skipString("'"); }
  else if (c === '{') { opens++; i++; }
  else if (c === '}') { closes++; i++; }
  else { i++; }
}

console.log('String-aware parse: { =', opens, '} =', closes, 'diff =', opens - closes);

// Now find the EXACT line
// Reset and scan line by line
let cumOpens = 0, cumCloses = 0;
i = 0;
for (let li = 0; li < vtLines.length; li++) {
  const lineStart = i;
  const lineContent = vtLines[li];
  const lineEnd = i + lineContent.length;

  let lineOpens = 0, lineCloses = 0;
  const startI = i;
  const endI = i + lineContent.length;

  // Just count for this line
  let j = i;
  while (j < endI) {
    const c = vtContent[j];
    if (c === '`') {
      // skip to end of template (simplified - just skip, we handled above)
      j++;
      while (j < vtContent.length && vtContent[j] !== '`') {
        if (vtContent[j] === '$' && vtContent[j+1] === '{') {
          j += 2;
          let d2 = 1;
          while (j < vtContent.length && d2 > 0) {
            if (vtContent[j] === '{') d2++;
            if (vtContent[j] === '}') d2--;
            j++;
          }
        } else if (vtContent[j] === '\\') {
          j += 2;
        } else {
          j++;
        }
      }
      j++; // skip closing `
    } else if (c === '"') {
      j++;
      while (j < vtContent.length && vtContent[j] !== '"') {
        if (vtContent[j] === '\\') j++;
        j++;
      }
      j++;
    } else if (c === "'") {
      j++;
      while (j < vtContent.length && vtContent[j] !== "'") {
        if (vtContent[j] === '\\') j++;
        j++;
      }
      j++;
    } else if (c === '{') {
      lineOpens++;
      j++;
    } else if (c === '}') {
      lineCloses++;
      j++;
    } else {
      j++;
    }
  }
  i = j + 1; // +1 for the \n

  cumOpens += lineOpens;
  cumCloses += lineCloses;

  if (lineOpens !== lineCloses) {
    console.log(`VT L${li+1} (HTML ${li+858}): +${lineOpens}-${lineCloses}=${lineOpens-lineCloses} cum=${cumOpens-cumCloses}: ${lineContent.trim().slice(0,60)}`);
  }
}
console.log('Final cum diff:', cumOpens - cumCloses);
