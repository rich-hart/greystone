def amortize_loan(P, r, n): #From wikipedia
    A = P * ((r*(1+r)**n)/ (((1+r)**n)-1))
    return A

# From https://www.educba.com/amortized-loan-formula/
def principal_repayment(P, r, n, t):
    return P * (r/n) * ((1 + r/n) ** (t*n)) / ((1+r/n) ** (t*n) -1 ) - P * (r/n)

def interest_payment(P, r, n):
    return P * r / n

#def total_repayment(principal, interest):
#    return principal + interest
