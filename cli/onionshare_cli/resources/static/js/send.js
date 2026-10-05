/**
 * Function to convert human-readable sizes back to bytes, for sorting
 * @param text {string}
 * @returns {string}
 */
function unhumanize(text) {
  var powers = {'b': 0, 'k': 1, 'm': 2, 'g': 3, 't': 4};
  var regex = /(\d+(?:\.\d+)?)\s?(B|K|M|G|T)?/i;
  var res = regex.exec(text);
  if (res[2] === undefined) {
    // Account for alphabetical words (file/dir names)
    return text;
  } else {
    return res[1] * Math.pow(1024, powers[res[2].toLowerCase()]);
  }
}

/**
 * @param n {number}
 */
function sortTable(n) {
  var i = 0;
  var shouldSwitch = false;
  var switchcount = 0;

  const table = document.getElementById("file-list");
  var switching = true;

  // Set the sorting direction to ascending:
  var dir = "asc";

  /* Make a loop that will continue until
    no switching has been done: */
  while (switching) {
    // Start by saying: no switching is done:
    switching = false;
    const rows = table.getElementsByClassName("row");
    /* Loop through all table rows (except the
      first, which contains table headers): */
    for (i = 1; i < (rows.length - 1); i++) {
      // Start by saying there should be no switching:
      shouldSwitch = false;
      /* Get the two elements you want to compare,
        one from current row and one from the next: */
      let x = rows[i].getElementsByClassName("cell-data")[n];
      let y = rows[i + 1].getElementsByClassName("cell-data")[n];

      let valX = x.classList.contains("size") ? unhumanize(x.innerHTML.toLowerCase()) : x.innerHTML;
      let valY = y.classList.contains("size") ? unhumanize(y.innerHTML.toLowerCase()) : y.innerHTML;

      /* Check if the two rows should switch place,
      based on the direction, asc or desc: */
      if (dir === "asc") {
        if (valX > valY) {
          // If so, mark as a switch and break the loop:
          shouldSwitch = true;
          break;
        }
      } else if (dir === "desc") {
        if (valX < valY) {
          // If so, mark as a switch and break the loop:
          shouldSwitch = true;
          break;
        }
      }
    }
  
    if (shouldSwitch) {
      /* If a switch has been marked, make the switch
      and mark that a switch has been done: */
      rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
      switching = true;
      // Each time a switch is done, increase this count by 1:
      switchcount++;
    } else {
      /* If no switching has been done AND the direction is "asc",
      set the direction to "desc" and run the while loop again. */
      if (switchcount === 0 && dir === "asc") {
        dir = "desc";
        switching = true;
      }
    }
  }
}

// Set click handlers
document.getElementById("filename-header").addEventListener("click", function(){
  sortTable(0);
});

document.getElementById("size-header").addEventListener("click", function(){
  sortTable(1);
});
