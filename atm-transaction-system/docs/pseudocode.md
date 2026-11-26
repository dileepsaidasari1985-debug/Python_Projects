# Pseudocode

## 1. Balance Inquiry
```text
PROCEDURE BalanceInquiry(account_number)
    account <- FetchAccountFromDB(account_number)
    transactions <- FetchTransactionsFromDB(account_number)
    summary <- CalculateSummary(transactions, account.initial_balance, account.current_balance)
    daily_used <- FetchTodayWithdrawals(account_number)
    remaining_daily <- MAX(0, settings.max_daily_withdrawal - daily_used)
    DISPLAY account.holder_name, account.account_number, account.current_balance,
            summary.total_money_deposited, summary.total_money_withdrawn, remaining_daily
END PROCEDURE
```

## 2. Transaction Validation (Deposit & Withdrawal)
```text
FUNCTION ValidateTransaction(txn_type, raw_amount, balance, daily_used, settings)
    (is_num, amount, err) <- ParseNumericAmount(raw_amount)
    IF NOT is_num THEN
        RETURN (FALSE, 0.0, err)
    END IF

    IF amount <= 0 THEN
        RETURN (FALSE, amount, "Amount must be greater than zero")
    END IF

    IF txn_type == "DEPOSIT" THEN
        RETURN (TRUE, amount, "")
    END IF

    // Withdrawal checks
    IF amount < settings.min_withdrawal THEN
        RETURN (FALSE, amount, "Below minimum withdrawal limit")
    ELSE IF amount > settings.max_per_transaction THEN
        RETURN (FALSE, amount, "Exceeds per-transaction limit")
    ELSE IF (amount MOD settings.denomination) != 0 OR amount != INT(amount) THEN
        RETURN (FALSE, amount, "Not a multiple of ATM denomination")
    ELSE IF amount > balance THEN
        RETURN (FALSE, amount, "Insufficient account balance")
    ELSE IF (daily_used + amount) > settings.max_daily_withdrawal THEN
        RETURN (FALSE, amount, "Exceeds daily withdrawal limit")
    END IF

    RETURN (TRUE, amount, "")
END FUNCTION
```

## 3. Deposit
```text
PROCEDURE ProcessDeposit(account_number, raw_amount, description)
    balance <- FetchBalance(account_number)
    (is_valid, amount, reason) <- ValidateTransaction("DEPOSIT", raw_amount, balance, 0, settings)
    txn_id <- GenerateTransactionID()
    IF is_valid THEN
        new_balance <- balance + amount
        status <- "SUCCESS"
    ELSE
        new_balance <- balance
        status <- "REJECTED"
    END IF
    SaveTransactionToSQLite(txn_id, "DEPOSIT", amount, balance, new_balance, status, reason, description)
    IF is_valid THEN UpdateAccountBalance(account_number, new_balance)
END PROCEDURE
```

## 4. Withdrawal
```text
PROCEDURE ProcessWithdrawal(account_number, raw_amount, description)
    balance <- FetchBalance(account_number)
    daily_used <- FetchTodayWithdrawals(account_number)
    (is_valid, amount, reason) <- ValidateTransaction("WITHDRAWAL", raw_amount, balance, daily_used, settings)
    txn_id <- GenerateTransactionID()
    IF is_valid THEN
        new_balance <- balance - amount
        status <- "SUCCESS"
    ELSE
        new_balance <- balance
        status <- "REJECTED"
    END IF
    SaveTransactionToSQLite(txn_id, "WITHDRAWAL", amount, balance, new_balance, status, reason, description)
    IF is_valid THEN UpdateAccountBalance(account_number, new_balance)
END PROCEDURE
```

## 5. Transaction Sequence Processing
```text
FUNCTION ProcessTransactionSequence(sequence_items, starting_balance, daily_used, settings)
    running_balance <- starting_balance
    running_daily <- daily_used
    nested_rows <- EMPTY LIST

    FOR step FROM 1 TO LENGTH(sequence_items) DO
        (txn_type, raw_amount, description) <- UNPACK sequence_items[step - 1]
        (is_valid, amount, reason) <- ValidateTransaction(txn_type, raw_amount, running_balance, running_daily, settings)
        balance_before <- running_balance
        txn_id <- GenerateTransactionID()

        IF is_valid THEN
            IF txn_type == "DEPOSIT" THEN
                running_balance <- running_balance + amount
            ELSE
                running_balance <- running_balance - amount
                running_daily <- running_daily + amount
            END IF
            status <- "SUCCESS"
        ELSE
            status <- "REJECTED"
        END IF

        APPEND [step, txn_id, txn_type, amount, balance_before, running_balance, status, reason] TO nested_rows
    END FOR

    RETURN nested_rows, running_balance
END FUNCTION
```

## 6. Transaction Summary Generation
```text
FUNCTION GenerateTransactionSummary(transactions, opening_balance, current_balance)
    total_deposited <- 0.0
    total_withdrawn <- 0.0
    success_count <- 0
    rejected_count <- 0
    largest_deposit <- 0.0
    largest_withdrawal <- 0.0
    successful_amounts <- EMPTY LIST

    FOR EACH txn IN transactions DO
        IF txn.status == "SUCCESS" THEN
            success_count <- success_count + 1
            APPEND txn.amount TO successful_amounts
            IF txn.type == "DEPOSIT" THEN
                total_deposited <- total_deposited + txn.amount
                IF txn.amount > largest_deposit THEN largest_deposit <- txn.amount
            ELSE
                total_withdrawn <- total_withdrawn + txn.amount
                IF txn.amount > largest_withdrawal THEN largest_withdrawal <- txn.amount
            END IF
        ELSE
            rejected_count <- rejected_count + 1
        END IF
    END FOR

    avg_amount <- (SUM(successful_amounts) / LENGTH(successful_amounts)) IF successful_amounts ELSE 0.0
    net_change <- current_balance - opening_balance
    RETURN SummaryObject(opening_balance, current_balance, total_deposited, total_withdrawn,
                         success_count, rejected_count, largest_deposit, largest_withdrawal,
                         avg_amount, net_change)
END FUNCTION
```
