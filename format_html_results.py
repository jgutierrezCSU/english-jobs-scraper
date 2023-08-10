import unicodedata


# TODO make font TH bold ( via inspect page / computed)
def create_html_file(df):

    # Encode non-ASCII characters for email compatibility
    df = df.applymap(
        lambda x: unicodedata.normalize("NFKD", str(x))
        .encode("ascii", "ignore")
        .decode("utf-8")
    )

    # Create the HTML table with checkboxes
    html_table = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <meta http-equiv="X-UA-Compatible" content="ie=edge">
      <!-- Bootstrap CSS -->
      <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css">
      <link href="https://fonts.googleapis.com/css?family=Roboto&display=swap" rel="stylesheet">  <!-- added -->

      <title>Job Results Table</title>
      <!-- added style-->
        <style>
             body {
        font-family: 'Times New Roman' , sans-serif;
              }
        </style>
    </head>
    <body>
      <div class="container mt-5">
        <table class="table" style="table-layout:fixed;width:100%" border="1" >
          <thead>
            <tr style="text-align:justify-all">
              <th scope="col" style="width:42px; text-align:center">#</th>
              <th style="width:30%">SUM_DETAILS</th>
              <th>MAIN_DETAILS</th>
              <th scope="col" style="width:90px">Actions</th>
            </tr>
          </thead>
          <tbody>
    """
    # Iterate through each row in the dataframe
    for index, row in df.iterrows():
        # Split the text at the string "LINKS:"
        title,company=row['title'],row['company']
        summary, link = row['summary'],row['link']
        location,distance,duration=row['location'],row['distance'],row['duration']

        # Create a row for each record in the DataFrame
        html_table += f"""
        <tr>
          <th scope="row"  style="text-align:right" >
            <input type="checkbox" class="form-check-input" id="row{index+1}">
          </th>
          <td style="max-width:300px;word-wrap:break-word">
          TITLE:   {title}<br> <br> 
          COMPANY:   {company}<br> <br>
          LOCATION:   {location}<br> <br>
          DISTANCE:   {distance}<br> <br>
          DURATION:   {duration}<br> <br>
          </td>
          <td style="max-width:300px;word-wrap:break-word">{row['summary']}  <br>
           LINK:  <a href="{link}">{link}</a></td>
          <td>
            <button type="button" class="btn btn-primary" onclick="hideRow('row{index+1}')">Hide</button>
          </td>
        </tr>
        """

    # Add the closing tags to the HTML table
    html_table += """
          </tbody>
        </table>
        <button type="button" class="btn btn-primary" onclick="hideCheckedRows()">Hide Checked Rows</button>
        <button type="button" class="btn btn-primary" onclick="showAllRows()">Show All Rows</button>
      </div>
      <!-- jQuery -->
      <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js"></script>
      <!-- Bootstrap JS -->
      <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js"></script>
      <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js"></script>
      <script>
        function hideRow(rowId) {
          document.getElementById(rowId).closest('tr').style.display = 'none';
        }
        function hideCheckedRows() {
          var checkboxes = document.querySelectorAll('input[type="checkbox"]');
          for (var i = 0; i < checkboxes.length; i++) {
            if (checkboxes[i].checked) {
              checkboxes[i].closest('tr').style.display = 'none';
            }
          }
        }
                function showAllRows() {
                var rows = document.querySelectorAll('tr');
            rows.forEach(function(row) {
                row.style.display = '';
            });
            }
        </script>
        </body>
            </html>
            """
    with open("results.html", "w") as f:
        f.write(html_table)
