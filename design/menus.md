// Main Menu
```
Main Menu
----------

Options:
> View Predictions
  View Results
  Create New Prediction
  Edit Prediction
  Exit
```


// View Predictions
```
Current Predictions
-------------------
Symbol    Trading-Pair    Start Date    Start Price   End Price   End Date    Buy Price   Sell Price
    xx          xxxxxx      xx-xx-xx            $xx         $xx   xx-xx-xx          $xx          $xx
    xx          xxxxxx      xx-xx-xx            $xx         $xx   xx-xx-xx          $xx          $xx
    xx          xxxxxx      xx-xx-xx            $xx         $xx   xx-xx-xx          $xx          $xx
    ...

Options:
> Return to Main Menu
  Exit
```

// View Results
```
Results
--------
Symbol    Trading-Pair    Start Date    Start Price   End Price   Act. End Price    End Date    Buy Price   Sell Price
    xx          xxxxxx      xx-xx-xx            $xx         $xx              $xx    xx-xx-xx          $xx          $xx
    xx          xxxxxx      xx-xx-xx            $xx         $xx              $xx    xx-xx-xx          $xx          $xx
    xx          xxxxxx      xx-xx-xx            $xx         $xx              $xx    xx-xx-xx          $xx          $xx
    ...

Options:
> Return to Main Menu
  Exit
```

// Create Prediction
```
New Prediction
--------------
Trading Pair:            // default: None (required)
Start Date (xx-xx-xx):   // default: Current date | Formats: xx/xx/xxxx, xx/xx/xx, xx-xx-xxxx, xx-xx-xx
End Date (xx-xx-xx):     // default: 7 days from current date
Starting Price ($xx):    // default: Price returned by API | Formats: $xx.xx, $xx, $.xx
Predicted End Price:     // default: None (required)
Set Buy/Sell Limit Prices (y/n):    // default: yes
'' If yes
Buy Price ($xx):         // default: None (required)
Sell Price ($xx):        // default: None (required)
'' After yes or If no

Summary
-------
[trading_pair]      
Start: [start_date]    [end_date]
End:   [start_price]   [end_price]
Buy:   [buy_price]
Sell:  [sell_price]
Save? (y/n):             // default: None (required)
```

// Option Format:
```
'' Vertical navigation: UP - [UP_KEY, 'w'], DOWN - [DOWN_KEY, 's'a]
''  - Enter key for selection of current choice
Options:
> option_1
  option_2
  option_3
  ...

'' Horizontal navigation: LEFT - [LEFT_KEY, 'a'], RIGHT - [RIGHT_KEY, 'd']
''  - Enter key for selection of current choice or by pressing character associated with option
> (char_1)option_1      (char_2)option_2      (char_3)option_3      ...

```