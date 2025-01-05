-- setup game
main = do
  -- get size of dictionary
  let size = length mediumDict
  putStrLn "\n\nWelcome to Evil Hangman!\n\n"
  putStrLn ("The small dictionary contains " ++ show size ++ " words")
  -- get new dict of words of the same size
  putStrLn "Word length (Must be 4 for this demo)?"
  wordLIO <- getLine
  let wordL = read wordLIO :: Int
  let dict = filter ((== wordL) . length) mediumDict
  -- set num of guesses
  putStrLn "Number of guesses?"
  guessesIO <- getLine
  let turns = read guessesIO :: Int
  let progress = getProgress wordL

  -- start playing game
  doTurn turns dict "" progress

getProgress 0 = []
getProgress size = '-' : getProgress (size - 1)

doTurn turnsLeft dict ls progress = do
  putStrLn ("\n\nYou have " ++ show turnsLeft ++ " guesses left.")
  putStrLn ("Letters guessed: " ++ show ls)
  putStrLn ("Word: " ++ progress)
  putStrLn "Guess a letter:"
  lIO <- getLine
  let l = head lIO
  let guesses = l : ls
  let matchingWords = simplify guesses dict
  let longestTuple = findLongestTuple matchingWords
  let newDict = snd longestTuple
  let newCase = fst longestTuple
  --mapM (\(x, y) -> putStrLn ("    " ++ x ++ " matches " ++ show y)) matchingWords
  --putStrLn ("  Using pattern " ++ newCase ++ " which matches " ++ show (length newDict) ++ " words")

  -- check for win
  if filter (=='-') newCase == ""
    then finished (fst (head matchingWords))
    else continue turnsLeft newDict guesses newCase lIO progress

continue turnsLeft newDict guesses newCase lIO progress = do
  -- print if guess was good or not
  if progress == newCase
    then putStrLn ("Sorry there's no " ++ lIO ++ "'s")
    else putStrLn "Good Guess!"
  -- start new turn
  if turnsLeft <= 1
    then noGuesses (head newDict)
    else doTurn (turnsLeft - 1) newDict guesses newCase

finished word = do
  putStrLn ("\nYou guessed it! The word was " ++ show word)

findLongestTuple [] = error "Cannot have empty list"
-- Call fltJR with the first tuple and the rest of the list.
findLongestTuple (x : xs) = findLongestList x xs
  where
    -- recursively returns the tuple with the longest list until the longest is known
    findLongestList t [] = t
    findLongestList t (u : us)
      -- if T has a longer list call with t as new longest
      | length (snd t) >= length (snd u) = findLongestList t us
      | otherwise = findLongestList u us

noGuesses answer = do
  putStrLn ("You are out of guesses :(\nThe answer was " ++answer)

-- removes duplicates of everything given from checkguess
simplify guesses dict = helper [] (checkGuess guesses dict)
  where
    helper seen [] = seen
    helper seen (x : xs)
      | contains x seen = helper (replace x seen) xs
      | otherwise = helper (seen ++ [x]) xs
    contains x [] = False
    contains x (y : ys)
      | fst x == fst y = True
      | otherwise = contains x ys
    replace x [] = [x]
    replace x (seen : seens)
      | fst x == fst seen = (fst seen, snd seen ++ snd x) : seens
      | otherwise = seen : replace x seens

checkGuess ls = concatMap (\w -> map (match w) [ls])

match word ls = (myFilter (`elem` ls) word, [word])
  where
    myFilter f = map (\c -> if f c then c else '-')

mediumDict = ["abbe", "abed", "abet", "able", "abye", "aced", "aces", "ache", "acme", "acne", "acre", "adze", "aeon", "aero", "aery", "aged", "agee", "ager", "ages", "ague", "ahem", "aide", "ajee", "akee", "alae", "alec", "alee", "alef", "ales", "alme", "aloe", "amen", "amie", "anes", "anew", "ante", "aped", "aper", "apes", "apex", "apse", "area", "ares", "arse", "asea", "ates", "aver", "aves", "awed", "awee", "awes", "axed", "axel", "axes", "axle", "ayes", "babe", "bade", "bake", "bale", "bane", "bare", "base", "bate", "bead", "beak", "beam", "bean", "bear", "beat", "beau", "bema", "beta", "blae", "brae", "cade", "cafe", "cage", "cake", "came", "cane", "cape", "care", "case", "cate", "cave", "ceca", "dace", "dale", "dame", "dare", "date", "daze", "dead", "deaf", "deal", "dean", "dear", "deva", "each", "earl", "earn", "ears", "ease", "east", "easy", "eath", "eats", "eaux", "eave", "egad", "egal", "elan", "epha", "eras", "etas", "etna", "exam", "eyas", "eyra", "face", "fade", "fake", "fame", "fane", "fare", "fate", "faze", "feal", "fear", "feat", "feta", "flea", "frae", "gaed", "gaen", "gaes", "gage", "gale", "game", "gane", "gape", "gate", "gave", "gaze", "gear", "geta", "hade", "haed", "haem", "haen", "haes", "haet", "hake", "hale", "hame", "hare", "hate", "have", "haze", "head", "heal", "heap", "hear", "heat", "idea", "ilea", "jade", "jake", "jane", "jape", "jean", "kaes", "kale", "kame", "kane", "keas", "lace", "lade", "lake", "lame", "lane", "lase", "late", "lave", "laze", "lead", "leaf", "leak", "leal", "lean", "leap", "lear", "leas", "leva", "mabe", "mace", "made", "maes", "mage", "make", "male", "mane", "mare", "mate", "maze", "mead", "meal", "mean", "meat", "mesa", "meta", "nabe", "name", "nape", "nave", "neap", "near", "neat", "nema", "odea", "olea", "pace", "page", "pale", "pane", "pare", "pase", "pate", "pave", "peag", "peak", "peal", "pean", "pear", "peas", "peat", "plea", "race", "rage", "rake", "rale", "rare", "rase", "rate", "rave", "raze", "read", "real", "ream", "reap", "rear", "rhea", "sabe", "sade", "safe", "sage", "sake", "sale", "same", "sane", "sate", "save", "seal", "seam", "sear", "seas", "seat", "sera", "seta", "shea", "spae", "tace", "tael", "take", "tale", "tame", "tape", "tare", "tate", "teak", "teal", "team", "tear", "teas", "teat", "tela", "tepa", "thae", "toea", "twae", "urea", "uvea", "vale", "vane", "vase", "veal", "vela", "vena", "vera", "wade", "waes", "wage", "wake", "wale", "wame", "wane", "ware", "wave", "weak", "weal", "wean", "wear", "weka", "yare", "yeah", "yean", "year", "yeas", "zeal", "zeta", "zoea"]