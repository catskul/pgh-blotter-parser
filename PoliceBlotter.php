<html>
    <head>
        <meta charset="UTF-8">
        <title>Police Blotter</title>
    </head>
    <body>
        <?php
        date_default_timezone_set("America/New_York");
        $day[0] = "sunday";
        $day[1] = "monday";
        $day[2] = "tuesday";
        $day[3] = "wednesday";
        $day[4] = "thursday";
        $day[5] = "friday";
        $day[6] = "saturday";
        $curlprefix = "http://www.city.pittsburgh.pa.us/police/blotter/blotter_";
        $pdfsuffix = ".pdf";

        $fpsuffix = "blotter_";

        $LT = localtime();
        $DOW = $LT[6] - 1;
        if ($DOW < 0) {
            $DOW = 6;
        }
        $weekday = strtolower($day[$DOW]);
        echo "Yesterday DOW " . date($DOW);
        echo "<br>";
        echo "Yesterday DOW " . $day[$DOW];
        echo "<br>";

        $YESTERDAY = mktime(0, 0, 0, date("m"), date("d") - 1, date("Y"));
        $YESTERDAYSUFFIX = date("Ymd", $YESTERDAY);
        //echo $YESTERDAYSUFFIX;
        //echo "<br>";
        //echo "Yesterday was " . date("Ymd", $YESTERDAY);
        //echo "<br>";


        $curlurl = curl_init("$curlprefix$day[$DOW]$pdfsuffix");
        $URL = "$fpsuffix$day[$DOW]$YESTERDAYSUFFIX$pdfsuffix";
        $fp = fopen($URL, "w+");

        //echo $URL;
        //echo "<br>";
        curl_setopt($curlurl, CURLOPT_FILE, $fp);
        curl_setopt($curlurl, CURLOPT_HEADER, 0);
        curl_exec($curlurl);
        curl_close($curlurl);
        fclose($fp);

        $PREFIX = "blotter_";
        $TXTSuffix = ".txt";
        $PDFSuffix = ".pdf";
        $PDFBLOTTER = $PREFIX . $weekday . date("Ymd", $YESTERDAY) . $PDFSuffix;
        $TXTBLOTTER = $PREFIX . $weekday . date("Ymd", $YESTERDAY) . $TXTSuffix;


        echo "<br>";
        echo "PDF " . $PDFBLOTTER;
        echo "<br>";
        echo "TXT " . $TXTBLOTTER;
        echo "<br>";
        $CMD = "python BlotterParser.py -i " . $PDFBLOTTER . " -o " . $TXTBLOTTER;
        echo $CMD;
        echo "<br>";
        $COMPARE = "python BlotterParser.py -i blotter_tuesday20140415.pdf -o blotter_tuesday20140415.txt";
        echo $COMPARE;
        echo "<br>";
        $RS = shell_exec($CMD);
        echo "CMD results" . $RS;
        echo "<br>";

        echo "Task Complete for " . $URL;
        
        ?>
    </body>
</html>
