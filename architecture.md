---                                                                                                                                                      
  Hackathon Presentation Script                                                                                                                            
                                                                                                                                                           
  ---                                                                                                                                                      
  INTRODUCTION                                                                                                                                             
                                                                                                                                                           
  ▎ "Show of hands — who here has made a bad crypto trade?"                                                                                                
                                                                                                                                                           
  (pause)                                                         
                                          
  ▎ "Yeah. We all have. The thing is, we know we messed up, but we never actually sit with it. We close the app, we move on, we tell ourselves it was a    
  learning experience.                                                                                                                                     
                                                                                                                                                           
  ▎ So we built Paper Hands Therapy.                                                                                                                       
                                                                  
  ▎ You enter your wallet. We fetch your entire on-chain history — every token you bought, every price you paid, every position you held too long or sold  
  too early. Then our AI, Dr. Rekt, sits you down and walks you through exactly what you did wrong. Chapter by chapter. Dollar by dollar.

  ▎ And the part that really hurts — Chapter 2. It shows you what you would have made if you'd just bought ETH or BTC on the exact same day you bought     
  whatever you bought. The exact dollar gap. The exact percentage. That number lives in your head.
                                                                                                                                                           
  ▎ It ends with an official psychiatric diagnosis. Condition, prognosis, treatment plan. Signed by Dr. Rekt.                                              
                                          
  ▎ It's a roast. But every single number in it is real."                                                                                                  
                                                                                                                                                           
  ---
  ARCHITECTURE                                                                                                                                             
                                                                  
  ▎ "Under the hood, this is a GoldRush-powered data pipeline.                                                                                             
                                                                  
  ▎ The moment you submit a wallet, our FastAPI backend figures out if it's an EVM wallet or Solana, and takes a different path for each.
                                          
  ▎ For EVM wallets — say, an Ethereum address — we first hit the GoldRush Streaming API, calling upnlForWallet. Think of this as the smart path: it comes 
  back with everything — your cost basis per token, your average buy and sell prices, realized and unrealized PnL. One call, full picture.                 
                                                                                                                                                           
  ▎ But not every wallet has streaming data. So if it comes back empty, we automatically fall back to transactions_v3 — the raw transaction history — and  
  we parse the ERC20 transfer events ourselves to reconstruct what you bought and sold.
                                                                                                                                                           
  ▎ Either way, we always call portfolio_v2 to get fresh current prices, because we want the loss to be accurate to the second.                            
                                          
  ▎ Then for the what-if, we call pricing/historical_by_addresses_v2 — we pass it the date of your very first trade, and it tells us exactly what ETH and  
  BTC were worth that day. That's how we calculate the gap between what you did and what you should have done.                                             
   
  ▎ For Solana wallets, we use balances_v2 — current holdings — and build the same what-if comparison against SOL.                                         
                                                                  
  ▎ All of that feeds into Gemini 3.1 Flash Lite, which plays Dr. Rekt. The model is instructed to only use numbers from the data — no invented figures.   
  The output comes back structured, we parse it, and it goes straight to the frontend.                                                                     
   
  ▎ The whole pipeline runs in one request. You enter a wallet, you get a roast. Real data, real APIs, real damage."                                       
                                                                  
  ---                                                                                                                                                      
  Deliver the "show of hands" opener with confidence — it gets the room immediately. Then let the demo do the heavy lifting after the architecture section.
