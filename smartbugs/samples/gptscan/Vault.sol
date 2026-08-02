// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Minimal, deliberately vulnerable contract used as a GPTScan smoke test.
// It is intentionally small (few functions => few LLM calls => low cost) while
// containing two recognisable GPTScan scenarios.

interface IERC20 {
    function balanceOf(address) external view returns (uint256);
    function totalSupply() external view returns (uint256);
    function transferFrom(address, address, uint256) external returns (bool);
}

contract Vault {
    IERC20 public token;
    mapping(address => uint256) public shares;

    constructor(address _token) {
        token = IERC20(_token);
    }

    // MWE-200 style: LP token value/price derived from manipulable on-chain
    // reserves (balanceOf / totalSupply) -> flashloan price manipulation.
    function getLiquidityPrice() public view returns (uint256) {
        uint256 reserve = token.balanceOf(address(this));
        uint256 supply = token.totalSupply();
        uint256 price = supply == 0 ? 0 : (reserve * 1e18) / supply;
        return price;
    }

    // MWE-207 style: pulls tokens from an arbitrary `from` address with no
    // allowance/approval check from the owner.
    function sweep(address from, address to, uint256 amount) public {
        token.transferFrom(from, to, amount);
        shares[to] += amount;
    }
}
