// mwevariety_fixed: aus Web3Bugs-Originalquellen geflattet (siehe corpus_tools/build_fixed.py)
// SPDX-License-Identifier: MIT
pragma solidity 0.8.36;

// ---- C:\Users\Carlo\Desktop\Familie\Alex\Uni\BACHELORARBEIT\Github\BA\corpus_tools\vendor\83@0.8\@openzeppelin\contracts\utils\Context.sol ----
// license-stripped
// OpenZeppelin Contracts v4.4.1 (utils/Context.sol)



/**
 * @dev Provides information about the current execution context, including the
 * sender of the transaction and its data. While these are generally available
 * via msg.sender and msg.data, they should not be accessed in such a direct
 * manner, since when dealing with meta-transactions the account sending and
 * paying for execution may not be the actual sender (as far as an application
 * is concerned).
 *
 * This contract is only required for intermediate, library-like contracts.
 */
abstract contract Context {
    function _msgSender() internal view virtual returns (address) {
        return msg.sender;
    }

    function _msgData() internal view virtual returns (bytes calldata) {
        return msg.data;
    }
}

// ---- C:\Users\Carlo\Desktop\Familie\Alex\Uni\BACHELORARBEIT\Github\BA\corpus_tools\vendor\83@0.8\@openzeppelin\contracts\access\Ownable.sol ----
// license-stripped
// OpenZeppelin Contracts v4.4.1 (access/Ownable.sol)





/**
 * @dev Contract module which provides a basic access control mechanism, where
 * there is an account (an owner) that can be granted exclusive access to
 * specific functions.
 *
 * By default, the owner account will be the one that deploys the contract. This
 * can later be changed with {transferOwnership}.
 *
 * This module is used through inheritance. It will make available the modifier
 * `onlyOwner`, which can be applied to your functions to restrict their use to
 * the owner.
 */
abstract contract Ownable is Context {
    address private _owner;

    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    /**
     * @dev Initializes the contract setting the deployer as the initial owner.
     */
    constructor() {
        _transferOwnership(_msgSender());
    }

    /**
     * @dev Returns the address of the current owner.
     */
    function owner() public view virtual returns (address) {
        return _owner;
    }

    /**
     * @dev Throws if called by any account other than the owner.
     */
    modifier onlyOwner() {
        require(owner() == _msgSender(), "Ownable: caller is not the owner");
        _;
    }

    /**
     * @dev Leaves the contract without owner. It will not be possible to call
     * `onlyOwner` functions anymore. Can only be called by the current owner.
     *
     * NOTE: Renouncing ownership will leave the contract without an owner,
     * thereby removing any functionality that is only available to the owner.
     */
    function renounceOwnership() public virtual onlyOwner {
        _transferOwnership(address(0));
    }

    /**
     * @dev Transfers ownership of the contract to a new account (`newOwner`).
     * Can only be called by the current owner.
     */
    function transferOwnership(address newOwner) public virtual onlyOwner {
        require(newOwner != address(0), "Ownable: new owner is the zero address");
        _transferOwnership(newOwner);
    }

    /**
     * @dev Transfers ownership of the contract to a new account (`newOwner`).
     * Internal function without access restriction.
     */
    function _transferOwnership(address newOwner) internal virtual {
        address oldOwner = _owner;
        _owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }
}

// ---- C:\Users\Carlo\Desktop\Familie\Alex\Uni\BACHELORARBEIT\Github\BA\corpus_tools\vendor\83@0.8\@openzeppelin\contracts\token\ERC20\IERC20.sol ----
// license-stripped
// OpenZeppelin Contracts v4.4.1 (token/ERC20/IERC20.sol)



/**
 * @dev Interface of the ERC20 standard as defined in the EIP.
 */
interface IERC20 {
    /**
     * @dev Returns the amount of tokens in existence.
     */
    function totalSupply() external view returns (uint256);

    /**
     * @dev Returns the amount of tokens owned by `account`.
     */
    function balanceOf(address account) external view returns (uint256);

    /**
     * @dev Moves `amount` tokens from the caller's account to `recipient`.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * Emits a {Transfer} event.
     */
    function transfer(address recipient, uint256 amount) external returns (bool);

    /**
     * @dev Returns the remaining number of tokens that `spender` will be
     * allowed to spend on behalf of `owner` through {transferFrom}. This is
     * zero by default.
     *
     * This value changes when {approve} or {transferFrom} are called.
     */
    function allowance(address owner, address spender) external view returns (uint256);

    /**
     * @dev Sets `amount` as the allowance of `spender` over the caller's tokens.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * IMPORTANT: Beware that changing an allowance with this method brings the risk
     * that someone may use both the old and the new allowance by unfortunate
     * transaction ordering. One possible solution to mitigate this race
     * condition is to first reduce the spender's allowance to 0 and set the
     * desired value afterwards:
     * https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729
     *
     * Emits an {Approval} event.
     */
    function approve(address spender, uint256 amount) external returns (bool);

    /**
     * @dev Moves `amount` tokens from `sender` to `recipient` using the
     * allowance mechanism. `amount` is then deducted from the caller's
     * allowance.
     *
     * Returns a boolean value indicating whether the operation succeeded.
     *
     * Emits a {Transfer} event.
     */
    function transferFrom(
        address sender,
        address recipient,
        uint256 amount
    ) external returns (bool);

    /**
     * @dev Emitted when `value` tokens are moved from one account (`from`) to
     * another (`to`).
     *
     * Note that `value` may be zero.
     */
    event Transfer(address indexed from, address indexed to, uint256 value);

    /**
     * @dev Emitted when the allowance of a `spender` for an `owner` is set by
     * a call to {approve}. `value` is the new allowance.
     */
    event Approval(address indexed owner, address indexed spender, uint256 value);
}

// ---- C:\Users\Carlo\Desktop\Familie\Alex\Uni\BACHELORARBEIT\Github\BA\corpus_tools\vendor\83@0.8\@openzeppelin\contracts\utils\Address.sol ----
// license-stripped
// OpenZeppelin Contracts v4.4.1 (utils/Address.sol)



/**
 * @dev Collection of functions related to the address type
 */
library Address {
    /**
     * @dev Returns true if `account` is a contract.
     *
     * [IMPORTANT]
     * ====
     * It is unsafe to assume that an address for which this function returns
     * false is an externally-owned account (EOA) and not a contract.
     *
     * Among others, `isContract` will return false for the following
     * types of addresses:
     *
     *  - an externally-owned account
     *  - a contract in construction
     *  - an address where a contract will be created
     *  - an address where a contract lived, but was destroyed
     * ====
     */
    function isContract(address account) internal view returns (bool) {
        // This method relies on extcodesize, which returns 0 for contracts in
        // construction, since the code is only stored at the end of the
        // constructor execution.

        uint256 size;
        assembly {
            size := extcodesize(account)
        }
        return size > 0;
    }

    /**
     * @dev Replacement for Solidity's `transfer`: sends `amount` wei to
     * `recipient`, forwarding all available gas and reverting on errors.
     *
     * https://eips.ethereum.org/EIPS/eip-1884[EIP1884] increases the gas cost
     * of certain opcodes, possibly making contracts go over the 2300 gas limit
     * imposed by `transfer`, making them unable to receive funds via
     * `transfer`. {sendValue} removes this limitation.
     *
     * https://diligence.consensys.net/posts/2019/09/stop-using-soliditys-transfer-now/[Learn more].
     *
     * IMPORTANT: because control is transferred to `recipient`, care must be
     * taken to not create reentrancy vulnerabilities. Consider using
     * {ReentrancyGuard} or the
     * https://solidity.readthedocs.io/en/v0.5.11/security-considerations.html#use-the-checks-effects-interactions-pattern[checks-effects-interactions pattern].
     */
    function sendValue(address payable recipient, uint256 amount) internal {
        require(address(this).balance >= amount, "Address: insufficient balance");

        (bool success, ) = recipient.call{value: amount}("");
        require(success, "Address: unable to send value, recipient may have reverted");
    }

    /**
     * @dev Performs a Solidity function call using a low level `call`. A
     * plain `call` is an unsafe replacement for a function call: use this
     * function instead.
     *
     * If `target` reverts with a revert reason, it is bubbled up by this
     * function (like regular Solidity function calls).
     *
     * Returns the raw returned data. To convert to the expected return value,
     * use https://solidity.readthedocs.io/en/latest/units-and-global-variables.html?highlight=abi.decode#abi-encoding-and-decoding-functions[`abi.decode`].
     *
     * Requirements:
     *
     * - `target` must be a contract.
     * - calling `target` with `data` must not revert.
     *
     * _Available since v3.1._
     */
    function functionCall(address target, bytes memory data) internal returns (bytes memory) {
        return functionCall(target, data, "Address: low-level call failed");
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`], but with
     * `errorMessage` as a fallback revert reason when `target` reverts.
     *
     * _Available since v3.1._
     */
    function functionCall(
        address target,
        bytes memory data,
        string memory errorMessage
    ) internal returns (bytes memory) {
        return functionCallWithValue(target, data, 0, errorMessage);
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`],
     * but also transferring `value` wei to `target`.
     *
     * Requirements:
     *
     * - the calling contract must have an ETH balance of at least `value`.
     * - the called Solidity function must be `payable`.
     *
     * _Available since v3.1._
     */
    function functionCallWithValue(
        address target,
        bytes memory data,
        uint256 value
    ) internal returns (bytes memory) {
        return functionCallWithValue(target, data, value, "Address: low-level call with value failed");
    }

    /**
     * @dev Same as {xref-Address-functionCallWithValue-address-bytes-uint256-}[`functionCallWithValue`], but
     * with `errorMessage` as a fallback revert reason when `target` reverts.
     *
     * _Available since v3.1._
     */
    function functionCallWithValue(
        address target,
        bytes memory data,
        uint256 value,
        string memory errorMessage
    ) internal returns (bytes memory) {
        require(address(this).balance >= value, "Address: insufficient balance for call");
        require(isContract(target), "Address: call to non-contract");

        (bool success, bytes memory returndata) = target.call{value: value}(data);
        return verifyCallResult(success, returndata, errorMessage);
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`],
     * but performing a static call.
     *
     * _Available since v3.3._
     */
    function functionStaticCall(address target, bytes memory data) internal view returns (bytes memory) {
        return functionStaticCall(target, data, "Address: low-level static call failed");
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-string-}[`functionCall`],
     * but performing a static call.
     *
     * _Available since v3.3._
     */
    function functionStaticCall(
        address target,
        bytes memory data,
        string memory errorMessage
    ) internal view returns (bytes memory) {
        require(isContract(target), "Address: static call to non-contract");

        (bool success, bytes memory returndata) = target.staticcall(data);
        return verifyCallResult(success, returndata, errorMessage);
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`],
     * but performing a delegate call.
     *
     * _Available since v3.4._
     */
    function functionDelegateCall(address target, bytes memory data) internal returns (bytes memory) {
        return functionDelegateCall(target, data, "Address: low-level delegate call failed");
    }

    /**
     * @dev Same as {xref-Address-functionCall-address-bytes-string-}[`functionCall`],
     * but performing a delegate call.
     *
     * _Available since v3.4._
     */
    function functionDelegateCall(
        address target,
        bytes memory data,
        string memory errorMessage
    ) internal returns (bytes memory) {
        require(isContract(target), "Address: delegate call to non-contract");

        (bool success, bytes memory returndata) = target.delegatecall(data);
        return verifyCallResult(success, returndata, errorMessage);
    }

    /**
     * @dev Tool to verifies that a low level call was successful, and revert if it wasn't, either by bubbling the
     * revert reason using the provided one.
     *
     * _Available since v4.3._
     */
    function verifyCallResult(
        bool success,
        bytes memory returndata,
        string memory errorMessage
    ) internal pure returns (bytes memory) {
        if (success) {
            return returndata;
        } else {
            // Look for revert reason and bubble it up if present
            if (returndata.length > 0) {
                // The easiest way to bubble the revert reason is using memory via assembly

                assembly {
                    let returndata_size := mload(returndata)
                    revert(add(32, returndata), returndata_size)
                }
            } else {
                revert(errorMessage);
            }
        }
    }
}

// ---- C:\Users\Carlo\Desktop\Familie\Alex\Uni\BACHELORARBEIT\Github\BA\corpus_tools\vendor\83@0.8\@openzeppelin\contracts\token\ERC20\utils\SafeERC20.sol ----
// license-stripped
// OpenZeppelin Contracts v4.4.1 (token/ERC20/utils/SafeERC20.sol)






/**
 * @title SafeERC20
 * @dev Wrappers around ERC20 operations that throw on failure (when the token
 * contract returns false). Tokens that return no value (and instead revert or
 * throw on failure) are also supported, non-reverting calls are assumed to be
 * successful.
 * To use this library you can add a `using SafeERC20 for IERC20;` statement to your contract,
 * which allows you to call the safe operations as `token.safeTransfer(...)`, etc.
 */
library SafeERC20 {
    using Address for address;

    function safeTransfer(
        IERC20 token,
        address to,
        uint256 value
    ) internal {
        _callOptionalReturn(token, abi.encodeWithSelector(token.transfer.selector, to, value));
    }

    function safeTransferFrom(
        IERC20 token,
        address from,
        address to,
        uint256 value
    ) internal {
        _callOptionalReturn(token, abi.encodeWithSelector(token.transferFrom.selector, from, to, value));
    }

    /**
     * @dev Deprecated. This function has issues similar to the ones found in
     * {IERC20-approve}, and its usage is discouraged.
     *
     * Whenever possible, use {safeIncreaseAllowance} and
     * {safeDecreaseAllowance} instead.
     */
    function safeApprove(
        IERC20 token,
        address spender,
        uint256 value
    ) internal {
        // safeApprove should only be called when setting an initial allowance,
        // or when resetting it to zero. To increase and decrease it, use
        // 'safeIncreaseAllowance' and 'safeDecreaseAllowance'
        require(
            (value == 0) || (token.allowance(address(this), spender) == 0),
            "SafeERC20: approve from non-zero to non-zero allowance"
        );
        _callOptionalReturn(token, abi.encodeWithSelector(token.approve.selector, spender, value));
    }

    function safeIncreaseAllowance(
        IERC20 token,
        address spender,
        uint256 value
    ) internal {
        uint256 newAllowance = token.allowance(address(this), spender) + value;
        _callOptionalReturn(token, abi.encodeWithSelector(token.approve.selector, spender, newAllowance));
    }

    function safeDecreaseAllowance(
        IERC20 token,
        address spender,
        uint256 value
    ) internal {
        unchecked {
            uint256 oldAllowance = token.allowance(address(this), spender);
            require(oldAllowance >= value, "SafeERC20: decreased allowance below zero");
            uint256 newAllowance = oldAllowance - value;
            _callOptionalReturn(token, abi.encodeWithSelector(token.approve.selector, spender, newAllowance));
        }
    }

    /**
     * @dev Imitates a Solidity high-level call (i.e. a regular function call to a contract), relaxing the requirement
     * on the return value: the return value is optional (but if data is returned, it must not be false).
     * @param token The token targeted by the call.
     * @param data The call data (encoded using abi.encode or one of its variants).
     */
    function _callOptionalReturn(IERC20 token, bytes memory data) private {
        // We need to perform a low level call here, to bypass Solidity's return data size checking mechanism, since
        // we're implementing it ourselves. We use {Address.functionCall} to perform this call, which verifies that
        // the target address contains contract code and also asserts for success in the low-level call.

        bytes memory returndata = address(token).functionCall(data, "SafeERC20: low-level call failed");
        if (returndata.length > 0) {
            // Return data is optional
            require(abi.decode(returndata, (bool)), "SafeERC20: ERC20 operation did not succeed");
        }
    }
}

// ---- C:\Users\Carlo\Desktop\Familie\Alex\Uni\BACHELORARBEIT\Github\BA\corpus_tools\vendor\83@0.8\@openzeppelin\contracts\security\ReentrancyGuard.sol ----
// license-stripped
// OpenZeppelin Contracts v4.4.1 (security/ReentrancyGuard.sol)



/**
 * @dev Contract module that helps prevent reentrant calls to a function.
 *
 * Inheriting from `ReentrancyGuard` will make the {nonReentrant} modifier
 * available, which can be applied to functions to make sure there are no nested
 * (reentrant) calls to them.
 *
 * Note that because there is a single `nonReentrant` guard, functions marked as
 * `nonReentrant` may not call one another. This can be worked around by making
 * those functions `private`, and then adding `external` `nonReentrant` entry
 * points to them.
 *
 * TIP: If you would like to learn more about reentrancy and alternative ways
 * to protect against it, check out our blog post
 * https://blog.openzeppelin.com/reentrancy-after-istanbul/[Reentrancy After Istanbul].
 */
abstract contract ReentrancyGuard {
    // Booleans are more expensive than uint256 or any type that takes up a full
    // word because each write operation emits an extra SLOAD to first read the
    // slot's contents, replace the bits taken up by the boolean, and then write
    // back. This is the compiler's defense against contract upgrades and
    // pointer aliasing, and it cannot be disabled.

    // The values being non-zero value makes deployment a bit more expensive,
    // but in exchange the refund on every call to nonReentrant will be lower in
    // amount. Since refunds are capped to a percentage of the total
    // transaction's gas, it is best to keep them low in cases like this one, to
    // increase the likelihood of the full refund coming into effect.
    uint256 private constant _NOT_ENTERED = 1;
    uint256 private constant _ENTERED = 2;

    uint256 private _status;

    constructor() {
        _status = _NOT_ENTERED;
    }

    /**
     * @dev Prevents a contract from calling itself, directly or indirectly.
     * Calling a `nonReentrant` function from another `nonReentrant`
     * function is not supported. It is possible to prevent this from happening
     * by making the `nonReentrant` function external, and making it call a
     * `private` function that does the actual work.
     */
    modifier nonReentrant() {
        // On the first call to nonReentrant, _notEntered will be true
        require(_status != _ENTERED, "ReentrancyGuard: reentrant call");

        // Any calls to nonReentrant after this point will fail
        _status = _ENTERED;

        _;

        // By storing the original value once again, a refund is triggered (see
        // https://eips.ethereum.org/EIPS/eip-2200)
        _status = _NOT_ENTERED;
    }
}

// ---- C:\Users\Carlo\Desktop\Familie\Alex\Uni\BACHELORARBEIT\Github\BA\corpus_tools\vendor\83@0.8\@openzeppelin\contracts\security\Pausable.sol ----
// license-stripped
// OpenZeppelin Contracts v4.4.1 (security/Pausable.sol)





/**
 * @dev Contract module which allows children to implement an emergency stop
 * mechanism that can be triggered by an authorized account.
 *
 * This module is used through inheritance. It will make available the
 * modifiers `whenNotPaused` and `whenPaused`, which can be applied to
 * the functions of your contract. Note that they will not be pausable by
 * simply including this module, only once the modifiers are put in place.
 */
abstract contract Pausable is Context {
    /**
     * @dev Emitted when the pause is triggered by `account`.
     */
    event Paused(address account);

    /**
     * @dev Emitted when the pause is lifted by `account`.
     */
    event Unpaused(address account);

    bool private _paused;

    /**
     * @dev Initializes the contract in unpaused state.
     */
    constructor() {
        _paused = false;
    }

    /**
     * @dev Returns true if the contract is paused, and false otherwise.
     */
    function paused() public view virtual returns (bool) {
        return _paused;
    }

    /**
     * @dev Modifier to make a function callable only when the contract is not paused.
     *
     * Requirements:
     *
     * - The contract must not be paused.
     */
    modifier whenNotPaused() {
        require(!paused(), "Pausable: paused");
        _;
    }

    /**
     * @dev Modifier to make a function callable only when the contract is paused.
     *
     * Requirements:
     *
     * - The contract must be paused.
     */
    modifier whenPaused() {
        require(paused(), "Pausable: not paused");
        _;
    }

    /**
     * @dev Triggers stopped state.
     *
     * Requirements:
     *
     * - The contract must not be paused.
     */
    function _pause() internal virtual whenNotPaused {
        _paused = true;
        emit Paused(_msgSender());
    }

    /**
     * @dev Returns to normal state.
     *
     * Requirements:
     *
     * - The contract must be paused.
     */
    function _unpause() internal virtual whenPaused {
        _paused = false;
        emit Unpaused(_msgSender());
    }
}

// ---- 83\contracts\external\ConvexInterfaces.sol ----
// license-stripped



interface ICvx {
    function reductionPerCliff() external view returns(uint256);
    function totalSupply() external view returns(uint256);
    function totalCliffs() external view returns(uint256);
    function maxSupply() external view returns(uint256);
}

interface IRewardStaking {
    struct PoolInfo {
        address lptoken;
        address token;
        address gauge;
        address crvRewards;
        address stash;
        bool shutdown;
    }

    function poolInfo(uint256) external view returns(PoolInfo memory);
    function stakeFor(address, uint256) external;
    function stake( uint256) external;
    function withdraw(uint256 amount, bool claim) external;
    function withdrawAndUnwrap(uint256 amount, bool claim) external;
    function earned(address account) external view returns (uint256);
    function getReward() external;
    function getReward(address _account, bool _claimExtras) external;
    function extraRewardsLength() external view returns (uint256);
    function extraRewards(uint256 _pid) external view returns (address);
    function rewardToken() external view returns (address);
    function balanceOf(address _account) external view returns (uint256);
}

interface IConvexDeposits {
    function deposit(uint256 _pid, uint256 _amount, bool _stake) external returns(bool);
    function deposit(uint256 _amount, bool _lock, address _stakeAddress) external;
}

// ---- 83\contracts\interfaces\IConcurRewardClaim.sol ----
// license-stripped



interface IConcurRewardClaim {
    function pushReward(
        address _recipient,
        address _token,
        uint256 _amount
    ) external;

    function claimRewards(address[] calldata _tokens) external;
}

// ---- C:\Users\Carlo\Desktop\Familie\Alex\Uni\BACHELORARBEIT\Github\BA\corpus_tools\vendor\83@0.8\@openzeppelin\contracts\utils\math\SafeMath.sol ----
// license-stripped
// OpenZeppelin Contracts v4.4.1 (utils/math/SafeMath.sol)



// CAUTION
// This version of SafeMath should only be used with Solidity 0.8 or later,
// because it relies on the compiler's built in overflow checks.

/**
 * @dev Wrappers over Solidity's arithmetic operations.
 *
 * NOTE: `SafeMath` is generally not needed starting with Solidity 0.8, since the compiler
 * now has built in overflow checking.
 */
library SafeMath {
    /**
     * @dev Returns the addition of two unsigned integers, with an overflow flag.
     *
     * _Available since v3.4._
     */
    function tryAdd(uint256 a, uint256 b) internal pure returns (bool, uint256) {
        unchecked {
            uint256 c = a + b;
            if (c < a) return (false, 0);
            return (true, c);
        }
    }

    /**
     * @dev Returns the substraction of two unsigned integers, with an overflow flag.
     *
     * _Available since v3.4._
     */
    function trySub(uint256 a, uint256 b) internal pure returns (bool, uint256) {
        unchecked {
            if (b > a) return (false, 0);
            return (true, a - b);
        }
    }

    /**
     * @dev Returns the multiplication of two unsigned integers, with an overflow flag.
     *
     * _Available since v3.4._
     */
    function tryMul(uint256 a, uint256 b) internal pure returns (bool, uint256) {
        unchecked {
            // Gas optimization: this is cheaper than requiring 'a' not being zero, but the
            // benefit is lost if 'b' is also tested.
            // See: https://github.com/OpenZeppelin/openzeppelin-contracts/pull/522
            if (a == 0) return (true, 0);
            uint256 c = a * b;
            if (c / a != b) return (false, 0);
            return (true, c);
        }
    }

    /**
     * @dev Returns the division of two unsigned integers, with a division by zero flag.
     *
     * _Available since v3.4._
     */
    function tryDiv(uint256 a, uint256 b) internal pure returns (bool, uint256) {
        unchecked {
            if (b == 0) return (false, 0);
            return (true, a / b);
        }
    }

    /**
     * @dev Returns the remainder of dividing two unsigned integers, with a division by zero flag.
     *
     * _Available since v3.4._
     */
    function tryMod(uint256 a, uint256 b) internal pure returns (bool, uint256) {
        unchecked {
            if (b == 0) return (false, 0);
            return (true, a % b);
        }
    }

    /**
     * @dev Returns the addition of two unsigned integers, reverting on
     * overflow.
     *
     * Counterpart to Solidity's `+` operator.
     *
     * Requirements:
     *
     * - Addition cannot overflow.
     */
    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        return a + b;
    }

    /**
     * @dev Returns the subtraction of two unsigned integers, reverting on
     * overflow (when the result is negative).
     *
     * Counterpart to Solidity's `-` operator.
     *
     * Requirements:
     *
     * - Subtraction cannot overflow.
     */
    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        return a - b;
    }

    /**
     * @dev Returns the multiplication of two unsigned integers, reverting on
     * overflow.
     *
     * Counterpart to Solidity's `*` operator.
     *
     * Requirements:
     *
     * - Multiplication cannot overflow.
     */
    function mul(uint256 a, uint256 b) internal pure returns (uint256) {
        return a * b;
    }

    /**
     * @dev Returns the integer division of two unsigned integers, reverting on
     * division by zero. The result is rounded towards zero.
     *
     * Counterpart to Solidity's `/` operator.
     *
     * Requirements:
     *
     * - The divisor cannot be zero.
     */
    function div(uint256 a, uint256 b) internal pure returns (uint256) {
        return a / b;
    }

    /**
     * @dev Returns the remainder of dividing two unsigned integers. (unsigned integer modulo),
     * reverting when dividing by zero.
     *
     * Counterpart to Solidity's `%` operator. This function uses a `revert`
     * opcode (which leaves remaining gas untouched) while Solidity uses an
     * invalid opcode to revert (consuming all remaining gas).
     *
     * Requirements:
     *
     * - The divisor cannot be zero.
     */
    function mod(uint256 a, uint256 b) internal pure returns (uint256) {
        return a % b;
    }

    /**
     * @dev Returns the subtraction of two unsigned integers, reverting with custom message on
     * overflow (when the result is negative).
     *
     * CAUTION: This function is deprecated because it requires allocating memory for the error
     * message unnecessarily. For custom revert reasons use {trySub}.
     *
     * Counterpart to Solidity's `-` operator.
     *
     * Requirements:
     *
     * - Subtraction cannot overflow.
     */
    function sub(
        uint256 a,
        uint256 b,
        string memory errorMessage
    ) internal pure returns (uint256) {
        unchecked {
            require(b <= a, errorMessage);
            return a - b;
        }
    }

    /**
     * @dev Returns the integer division of two unsigned integers, reverting with custom message on
     * division by zero. The result is rounded towards zero.
     *
     * Counterpart to Solidity's `/` operator. Note: this function uses a
     * `revert` opcode (which leaves remaining gas untouched) while Solidity
     * uses an invalid opcode to revert (consuming all remaining gas).
     *
     * Requirements:
     *
     * - The divisor cannot be zero.
     */
    function div(
        uint256 a,
        uint256 b,
        string memory errorMessage
    ) internal pure returns (uint256) {
        unchecked {
            require(b > 0, errorMessage);
            return a / b;
        }
    }

    /**
     * @dev Returns the remainder of dividing two unsigned integers. (unsigned integer modulo),
     * reverting with custom message when dividing by zero.
     *
     * CAUTION: This function is deprecated because it requires allocating memory for the error
     * message unnecessarily. For custom revert reasons use {tryMod}.
     *
     * Counterpart to Solidity's `%` operator. This function uses a `revert`
     * opcode (which leaves remaining gas untouched) while Solidity uses an
     * invalid opcode to revert (consuming all remaining gas).
     *
     * Requirements:
     *
     * - The divisor cannot be zero.
     */
    function mod(
        uint256 a,
        uint256 b,
        string memory errorMessage
    ) internal pure returns (uint256) {
        unchecked {
            require(b > 0, errorMessage);
            return a % b;
        }
    }
}

// ---- C:\Users\Carlo\Desktop\Familie\Alex\Uni\BACHELORARBEIT\Github\BA\corpus_tools\vendor\83@0.8\@openzeppelin\contracts\utils\math\SafeCast.sol ----
// license-stripped
// OpenZeppelin Contracts v4.4.1 (utils/math/SafeCast.sol)



/**
 * @dev Wrappers over Solidity's uintXX/intXX casting operators with added overflow
 * checks.
 *
 * Downcasting from uint256/int256 in Solidity does not revert on overflow. This can
 * easily result in undesired exploitation or bugs, since developers usually
 * assume that overflows raise errors. `SafeCast` restores this intuition by
 * reverting the transaction when such an operation overflows.
 *
 * Using this library instead of the unchecked operations eliminates an entire
 * class of bugs, so it's recommended to use it always.
 *
 * Can be combined with {SafeMath} and {SignedSafeMath} to extend it to smaller types, by performing
 * all math on `uint256` and `int256` and then downcasting.
 */
library SafeCast {
    /**
     * @dev Returns the downcasted uint224 from uint256, reverting on
     * overflow (when the input is greater than largest uint224).
     *
     * Counterpart to Solidity's `uint224` operator.
     *
     * Requirements:
     *
     * - input must fit into 224 bits
     */
    function toUint224(uint256 value) internal pure returns (uint224) {
        require(value <= type(uint224).max, "SafeCast: value doesn't fit in 224 bits");
        return uint224(value);
    }

    /**
     * @dev Returns the downcasted uint128 from uint256, reverting on
     * overflow (when the input is greater than largest uint128).
     *
     * Counterpart to Solidity's `uint128` operator.
     *
     * Requirements:
     *
     * - input must fit into 128 bits
     */
    function toUint128(uint256 value) internal pure returns (uint128) {
        require(value <= type(uint128).max, "SafeCast: value doesn't fit in 128 bits");
        return uint128(value);
    }

    /**
     * @dev Returns the downcasted uint96 from uint256, reverting on
     * overflow (when the input is greater than largest uint96).
     *
     * Counterpart to Solidity's `uint96` operator.
     *
     * Requirements:
     *
     * - input must fit into 96 bits
     */
    function toUint96(uint256 value) internal pure returns (uint96) {
        require(value <= type(uint96).max, "SafeCast: value doesn't fit in 96 bits");
        return uint96(value);
    }

    /**
     * @dev Returns the downcasted uint64 from uint256, reverting on
     * overflow (when the input is greater than largest uint64).
     *
     * Counterpart to Solidity's `uint64` operator.
     *
     * Requirements:
     *
     * - input must fit into 64 bits
     */
    function toUint64(uint256 value) internal pure returns (uint64) {
        require(value <= type(uint64).max, "SafeCast: value doesn't fit in 64 bits");
        return uint64(value);
    }

    /**
     * @dev Returns the downcasted uint32 from uint256, reverting on
     * overflow (when the input is greater than largest uint32).
     *
     * Counterpart to Solidity's `uint32` operator.
     *
     * Requirements:
     *
     * - input must fit into 32 bits
     */
    function toUint32(uint256 value) internal pure returns (uint32) {
        require(value <= type(uint32).max, "SafeCast: value doesn't fit in 32 bits");
        return uint32(value);
    }

    /**
     * @dev Returns the downcasted uint16 from uint256, reverting on
     * overflow (when the input is greater than largest uint16).
     *
     * Counterpart to Solidity's `uint16` operator.
     *
     * Requirements:
     *
     * - input must fit into 16 bits
     */
    function toUint16(uint256 value) internal pure returns (uint16) {
        require(value <= type(uint16).max, "SafeCast: value doesn't fit in 16 bits");
        return uint16(value);
    }

    /**
     * @dev Returns the downcasted uint8 from uint256, reverting on
     * overflow (when the input is greater than largest uint8).
     *
     * Counterpart to Solidity's `uint8` operator.
     *
     * Requirements:
     *
     * - input must fit into 8 bits.
     */
    function toUint8(uint256 value) internal pure returns (uint8) {
        require(value <= type(uint8).max, "SafeCast: value doesn't fit in 8 bits");
        return uint8(value);
    }

    /**
     * @dev Converts a signed int256 into an unsigned uint256.
     *
     * Requirements:
     *
     * - input must be greater than or equal to 0.
     */
    function toUint256(int256 value) internal pure returns (uint256) {
        require(value >= 0, "SafeCast: value must be positive");
        return uint256(value);
    }

    /**
     * @dev Returns the downcasted int128 from int256, reverting on
     * overflow (when the input is less than smallest int128 or
     * greater than largest int128).
     *
     * Counterpart to Solidity's `int128` operator.
     *
     * Requirements:
     *
     * - input must fit into 128 bits
     *
     * _Available since v3.1._
     */
    function toInt128(int256 value) internal pure returns (int128) {
        require(value >= type(int128).min && value <= type(int128).max, "SafeCast: value doesn't fit in 128 bits");
        return int128(value);
    }

    /**
     * @dev Returns the downcasted int64 from int256, reverting on
     * overflow (when the input is less than smallest int64 or
     * greater than largest int64).
     *
     * Counterpart to Solidity's `int64` operator.
     *
     * Requirements:
     *
     * - input must fit into 64 bits
     *
     * _Available since v3.1._
     */
    function toInt64(int256 value) internal pure returns (int64) {
        require(value >= type(int64).min && value <= type(int64).max, "SafeCast: value doesn't fit in 64 bits");
        return int64(value);
    }

    /**
     * @dev Returns the downcasted int32 from int256, reverting on
     * overflow (when the input is less than smallest int32 or
     * greater than largest int32).
     *
     * Counterpart to Solidity's `int32` operator.
     *
     * Requirements:
     *
     * - input must fit into 32 bits
     *
     * _Available since v3.1._
     */
    function toInt32(int256 value) internal pure returns (int32) {
        require(value >= type(int32).min && value <= type(int32).max, "SafeCast: value doesn't fit in 32 bits");
        return int32(value);
    }

    /**
     * @dev Returns the downcasted int16 from int256, reverting on
     * overflow (when the input is less than smallest int16 or
     * greater than largest int16).
     *
     * Counterpart to Solidity's `int16` operator.
     *
     * Requirements:
     *
     * - input must fit into 16 bits
     *
     * _Available since v3.1._
     */
    function toInt16(int256 value) internal pure returns (int16) {
        require(value >= type(int16).min && value <= type(int16).max, "SafeCast: value doesn't fit in 16 bits");
        return int16(value);
    }

    /**
     * @dev Returns the downcasted int8 from int256, reverting on
     * overflow (when the input is less than smallest int8 or
     * greater than largest int8).
     *
     * Counterpart to Solidity's `int8` operator.
     *
     * Requirements:
     *
     * - input must fit into 8 bits.
     *
     * _Available since v3.1._
     */
    function toInt8(int256 value) internal pure returns (int8) {
        require(value >= type(int8).min && value <= type(int8).max, "SafeCast: value doesn't fit in 8 bits");
        return int8(value);
    }

    /**
     * @dev Converts an unsigned uint256 into a signed int256.
     *
     * Requirements:
     *
     * - input must be less than or equal to maxInt256.
     */
    function toInt256(uint256 value) internal pure returns (int256) {
        // Note: Unsafe cast below is okay because `type(int256).max` is guaranteed to be positive
        require(value <= uint256(type(int256).max), "SafeCast: value doesn't fit in an int256");
        return int256(value);
    }
}

// ---- 83\contracts\MasterChef.sol ----
// license-stripped











contract MasterChef is Ownable, ReentrancyGuard {
    using SafeMath for uint;
    using SafeERC20 for IERC20;

    event Deposit(address indexed _user, uint indexed _pid, uint _amount);
    event Withdraw(address indexed _user, uint indexed _pid, uint _amount);
    event EmergencyWithdraw(address indexed user, uint indexed _pid, uint _amount);

    struct UserInfo {
        uint128 amount; // How many tokens the user has provided.
        uint128 rewardDebt; // Reward debt. See explanation below.
        //
        // We do some fancy math here. Basically, any point in time, the amount of RADSs
        // entitled to a user but is pending to be distributed is:
        //
        //   pending reward = (user.amount * pool.accumlatedConcurPerShare) - user.rewardDebt
        //
        // Whenever a user deposits or withdraws LP tokens to a pool. Here's what happens:
        //   1. The pool's `accumlatedConcurPerShare` (and `lastRewardBlock`) gets updated.
        //   2. User receives the pending reward sent to his/her address.
        //   3. User's `amount` gets updated.
        //   4. User's `rewardDebt` gets updated.
    }

    // Info of each pool.
    struct PoolInfo {
        IERC20 depositToken; // Address of LP token contract.
        uint allocPoint; // How many allocation points assigned to this pool. to distribute per block.
        uint lastRewardBlock; // Last block number that distribution occurs.
        uint accConcurPerShare; // Accumulated per share, times multiplier. See below.
        uint16 depositFeeBP; // Deposit fee in basis points
    }

    PoolInfo[] public poolInfo;
    mapping(uint => mapping(address => UserInfo)) public userInfo; // Info of each user that stakes LP tokens.
    mapping(address => bool) public isDepositor;
    mapping(address => uint256) public pid; // pid mapped to token
    uint public concurPerBlock = 100000 gwei; // concur tokens transferred per block
    uint public totalAllocPoint = 0; // Total allocation points. Must be the sum of all allocation points in all pools.
    uint public startBlock;
    uint public endBlock; // The block number when mining starts.
    IERC20 public concur;

    uint private _concurShareMultiplier = 1e18;
    uint private _perMille = 1000; // 100%

    constructor(IERC20 _concur, uint _startBlock, uint _endBlock) Ownable() {
        startBlock = _startBlock;
        endBlock = _endBlock;
        concur = _concur;
        poolInfo.push(
            PoolInfo({
            depositToken: IERC20(address(0)),
            allocPoint : 0,
            lastRewardBlock : _startBlock,
            accConcurPerShare : 0,
            depositFeeBP : 0
        }));
    }

    modifier onlyDepositor() {
        require(isDepositor[msg.sender], "!depositor");
        _;
    }

    function addDepositor(address _depositor) external onlyOwner {
        isDepositor[_depositor] = true;
    }

    function removeDepositor(address _depositor) external onlyOwner {
        isDepositor[_depositor] = false;
    }

    function add(address _token, uint _allocationPoints, uint16 _depositFee, uint _startBlock) public onlyOwner {
        require(_token != address(0), "zero address");
        uint lastRewardBlock = block.number > _startBlock ? block.number : _startBlock;
        totalAllocPoint = totalAllocPoint.add(_allocationPoints);
        require(pid[_token] == 0, "already registered"); // pid starts from 0
        poolInfo.push(
            PoolInfo({
                depositToken: IERC20(_token),
                allocPoint: _allocationPoints,
                lastRewardBlock: lastRewardBlock,
                accConcurPerShare: 0,
                depositFeeBP: _depositFee
            })
        );
        pid[_token] = poolInfo.length - 1;
    }

    function poolLength() external view returns (uint) {
        return poolInfo.length;
    }

    // Return reward multiplier over the given _from to _to block.
    function getMultiplier(uint _from, uint _to) public pure returns (uint) {
        return _to.sub(_from);
    }

    // View function to see pending [concur] on frontend.
    function pendingConcur(uint _pid, address _user) external view returns (uint) {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][_user];
        uint accConcurPerShare = pool.accConcurPerShare;
        uint lpSupply = pool.depositToken.balanceOf(address(this));
        if (block.number > pool.lastRewardBlock && lpSupply != 0) {
            uint multiplier = getMultiplier(pool.lastRewardBlock, block.number);
            uint concurReward = multiplier.mul(concurPerBlock).mul(pool.allocPoint).div(totalAllocPoint);
            accConcurPerShare = accConcurPerShare.add(concurReward.mul(_concurShareMultiplier).div(lpSupply));
        }
        return user.amount * accConcurPerShare / _concurShareMultiplier - user.rewardDebt;
    }

    // Update reward variables for all pools. Be careful of gas spending!
    function massUpdatePools() public {
        uint length = poolInfo.length;
        for (uint _pid = 0; _pid < length; ++_pid) {
            updatePool(_pid);
        }
    }

    // Update reward variables of the given pool to be up-to-date.
    function updatePool(uint _pid) public {
        PoolInfo storage pool = poolInfo[_pid];
        if (block.number <= pool.lastRewardBlock) {
            return;
        }
        uint lpSupply = pool.depositToken.balanceOf(address(this));
        if (lpSupply == 0 || pool.allocPoint == 0) {
            pool.lastRewardBlock = block.number;
            return;
        }
        if(block.number >= endBlock) {
            pool.lastRewardBlock = block.number;
            return;
        }        

        uint multiplier = getMultiplier(pool.lastRewardBlock, block.number);
        uint concurReward = multiplier.mul(concurPerBlock).mul(pool.allocPoint).div(totalAllocPoint);
        pool.accConcurPerShare = pool.accConcurPerShare.add(concurReward.mul(_concurShareMultiplier).div(lpSupply));
        pool.lastRewardBlock = block.number;
    }

    // Deposit tokens for [concur] allocation.  
    function deposit(address _recipient, uint _pid, uint _amount) external nonReentrant onlyDepositor {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][_msgSender()];
        updatePool(_pid);
       
        if(user.amount > 0) {  
            uint pending = user.amount * pool.accConcurPerShare / _concurShareMultiplier - user.rewardDebt;
            if (pending > 0) {
                safeConcurTransfer(_recipient, pending);
            }
        }

        if (_amount > 0) {
            if (pool.depositFeeBP > 0) {
                uint depositFee = _amount.mul(pool.depositFeeBP).div(_perMille);
                user.amount = SafeCast.toUint128(user.amount + _amount - depositFee);
            } else {
                user.amount = SafeCast.toUint128(user.amount + _amount);
            }
        }     

        user.rewardDebt = SafeCast.toUint128(user.amount * pool.accConcurPerShare / _concurShareMultiplier);
        emit Deposit(_recipient, _pid, _amount);
    }

    // Withdraw tokens
    function withdraw(address _recipient, uint _pid, uint _amount) external nonReentrant onlyDepositor {
        PoolInfo storage pool = poolInfo[_pid];
        UserInfo storage user = userInfo[_pid][_msgSender()];
        require(user.amount > 0, "MasterChef: nothing to withdraw");
        require(user.amount >= _amount, "MasterChef: withdraw not allowed");
        updatePool(_pid);

        uint pending = user.amount * pool.accConcurPerShare / _concurShareMultiplier - user.rewardDebt;
        if(pending > 0) {
            safeConcurTransfer(_recipient, pending);
        }
        if (_amount > 0) {
            user.amount = SafeCast.toUint128(user.amount - _amount);
        }
        user.rewardDebt = SafeCast.toUint128(user.amount * pool.accConcurPerShare / _concurShareMultiplier);
        emit Withdraw(_recipient, _pid, _amount);
    }

    // Safe [concur] transfer function, just in case if rounding error causes pool to not have enough
    function safeConcurTransfer(address _to, uint _amount) private {
        uint concurBalance = concur.balanceOf(address(this));
        bool transferSuccess = false;
        if (_amount > concurBalance) {
            transferSuccess = concur.transfer(_to, concurBalance);
        } else {
            transferSuccess = concur.transfer(_to, _amount);
        }
        require(transferSuccess, "safeConcurTransfer: transfer failed");
    }
}

// ---- 83\contracts\ConvexStakingWrapper.sol ----
// license-stripped












contract ConvexStakingWrapper is Ownable, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;

    struct RewardType {
        address token;
        address pool;
        uint128 integral;
        uint128 remaining;
    }

    struct Reward {
        uint128 integral;
    }

    //constants/immutables
    address public constant convexBooster =
        address(0xF403C135812408BFbE8713b5A23a04b3D48AAE31);
    address public constant crv =
        address(0xD533a949740bb3306d119CC777fa900bA034cd52);
    address public constant cvx =
        address(0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B);

    uint256 public constant CRV_INDEX = 0;
    uint256 public constant CVX_INDEX = 1;
    uint256 public constant VOTECYCLE_START = 1645002000; //Feb 16 2022 09:00:00 GMT+0000
    MasterChef public immutable masterChef;

    //convex rewards
    mapping(uint256 => address) public convexPool;
    mapping(uint256 => RewardType[]) public rewards;
    mapping(uint256 => mapping(uint256 => mapping(address => Reward)))
        public userReward;
    mapping(uint256 => mapping(address => uint256)) public registeredRewards;

    //management
    address public treasury;
    IConcurRewardClaim public claimContract;

    struct Deposit {
        uint64 epoch;
        uint192 amount;
    }

    struct WithdrawRequest {
        uint64 epoch;
        uint192 amount;
    }

    mapping(address => uint256) public pids;
    mapping(uint256 => mapping(address => Deposit)) public deposits;
    mapping(uint256 => mapping(address => WithdrawRequest)) public withdrawRequest;

    event Deposited(address indexed _user, uint256 _amount);
    event Withdrawn(address indexed _user, uint256 _amount);

    constructor(address _treasury, MasterChef _masterChef) {
        treasury = _treasury;
        masterChef = _masterChef;
    }

    function pause() external onlyOwner {
        _pause();
    }

    function unpause() external onlyOwner {
        _unpause();
    }

    function changeTreasury(address _treasury) external onlyOwner {
        treasury = _treasury;
    }

    function setRewardPool(address _claimContract) external onlyOwner {
        claimContract = IConcurRewardClaim(_claimContract);
    }

    /// @notice function to bootstrap the reward pool and extra rewards of convex booster
    /// @dev should be able to be called more than once
    /// @param _pid pid of the curve lp. same as convex booster pid
    function addRewards(uint256 _pid) public {
        address mainPool = IRewardStaking(convexBooster)
            .poolInfo(_pid)
            .crvRewards;
        if (rewards[_pid].length == 0) {
            pids[IRewardStaking(convexBooster).poolInfo(_pid).lptoken] = _pid;
            convexPool[_pid] = mainPool;
            rewards[_pid].push(
                RewardType({
                    token: crv,
                    pool: mainPool,
                    integral: 0,
                    remaining: 0
                })
            );
            rewards[_pid].push(
                RewardType({
                    token: cvx,
                    pool: address(0),
                    integral: 0,
                    remaining: 0
                })
            );
            registeredRewards[_pid][crv] = CRV_INDEX + 1; //mark registered at index+1
            registeredRewards[_pid][cvx] = CVX_INDEX + 1; //mark registered at index+1
        }

        uint256 extraCount = IRewardStaking(mainPool).extraRewardsLength();
        for (uint256 i = 0; i < extraCount; i++) {
            address extraPool = IRewardStaking(mainPool).extraRewards(i);
            address extraToken = IRewardStaking(extraPool).rewardToken();
            if (extraToken == cvx) {
                //no-op for cvx, crv rewards
                rewards[_pid][CVX_INDEX].pool = extraPool;
            } else if (registeredRewards[_pid][extraToken] == 0) {
                //add new token to list
                rewards[_pid].push(
                    RewardType({
                        token: IRewardStaking(extraPool).rewardToken(),
                        pool: extraPool,
                        integral: 0,
                        remaining: 0
                    })
                );
                registeredRewards[_pid][extraToken] = rewards[_pid].length; //mark registered at index+1
            }
        }
    }

    function rewardLength(uint256 _pid) external view returns (uint256) {
        return rewards[_pid].length;
    }

    function _getDepositedBalance(uint256 _pid, address _account)
        internal
        view
        virtual
        returns (uint256)
    {
        return deposits[_pid][_account].amount;
    }

    function _getTotalSupply(uint256 _pid)
        internal
        view
        virtual
        returns (uint256)
    {
        return IRewardStaking(convexPool[_pid]).balanceOf(address(this));
    }

    function _calcRewardIntegral(
        uint256 _pid,
        uint256 _index,
        address _account,
        uint256 _balance,
        uint256 _supply
    ) internal {
        RewardType memory reward = rewards[_pid][_index];

        //get difference in balance and remaining rewards
        //getReward is unguarded so we use remaining to keep track of how much was actually claimed
        uint256 bal = IERC20(reward.token).balanceOf(address(this));
        uint256 d_reward = bal - reward.remaining;
        // send 20 % of cvx / crv reward to treasury
        if (reward.token == cvx || reward.token == crv) {
            IERC20(reward.token).transfer(treasury, d_reward / 5);
            d_reward = (d_reward * 4) / 5;
        }
        IERC20(reward.token).transfer(address(claimContract), d_reward);

        if (_supply > 0 && d_reward > 0) {
            reward.integral =
                reward.integral +
                uint128((d_reward * 1e20) / _supply);
        }

        //update user integrals
        uint256 userI = userReward[_pid][_index][_account].integral;
        if (userI < reward.integral) {
            userReward[_pid][_index][_account].integral = reward.integral;
            claimContract.pushReward(
                _account,
                reward.token,
                (_balance * (reward.integral - userI)) / 1e20
            );
        }

        //update remaining reward here since balance could have changed if claiming
        if (bal != reward.remaining) {
            reward.remaining = uint128(bal);
        }

        rewards[_pid][_index] = reward;
    }

    function _checkpoint(uint256 _pid, address _account) internal {
        //if shutdown, no longer checkpoint in case there are problems
        if (paused()) return;

        uint256 supply = _getTotalSupply(_pid);
        uint256 depositedBalance = _getDepositedBalance(_pid, _account);

        IRewardStaking(convexPool[_pid]).getReward(address(this), true);

        uint256 rewardCount = rewards[_pid].length;
        for (uint256 i = 0; i < rewardCount; i++) {
            _calcRewardIntegral(_pid, i, _account, depositedBalance, supply);
        }
    }

    /// @notice deposit curve lp token
    /// @dev should approve curve lp token to this address before calling this function
    /// @param _pid pid to deposit, uses same pid as convex booster
    /// @param _amount amount to withdraw
    function deposit(uint256 _pid, uint256 _amount)
        external
        whenNotPaused
        nonReentrant
    {
        _checkpoint(_pid, msg.sender);
        deposits[_pid][msg.sender].epoch = currentEpoch();
        deposits[_pid][msg.sender].amount += uint192(_amount);
        if (_amount > 0) {
            IERC20 lpToken = IERC20(
                IRewardStaking(convexPool[_pid]).poolInfo(_pid).lptoken
            );

            lpToken.safeTransferFrom(msg.sender, address(this), _amount);
            lpToken.safeApprove(convexBooster, _amount);
            IConvexDeposits(convexBooster).deposit(_pid, _amount, true);
            lpToken.safeApprove(convexBooster, 0);
            uint256 pid = masterChef.pid(address(lpToken));
            masterChef.deposit(msg.sender, pid, _amount);
        }

        emit Deposited(msg.sender, _amount);
    }

    /// @notice withdraw curve lp token
    /// @dev should request withdraw before calling this function
    /// @param _pid pid to withdraw, uses same pid as convex booster
    /// @param _amount amount to withdraw
    function withdraw(uint256 _pid, uint256 _amount) external nonReentrant {
        WithdrawRequest memory request = withdrawRequest[_pid][msg.sender];
        require(request.epoch < currentEpoch() && deposits[_pid][msg.sender].epoch + 1 < currentEpoch(), "wait");
        require(request.amount >= _amount, "too much");
        _checkpoint(_pid, msg.sender);
        deposits[_pid][msg.sender].amount -= uint192(_amount);
        if (_amount > 0) {
            IRewardStaking(convexPool[_pid]).withdrawAndUnwrap(_amount, false);
            IERC20 lpToken = IERC20(
                IRewardStaking(convexPool[_pid]).poolInfo(_pid).lptoken
            );
            lpToken.safeTransfer(msg.sender, _amount);
            uint256 pid = masterChef.pid(address(lpToken));
            masterChef.withdraw(msg.sender, pid, _amount);
        }
        delete withdrawRequest[_pid][msg.sender];
        //events
        emit Withdrawn(msg.sender, _amount);
    }

    /// @notice epoch for voting cycle
    /// @return returns the epoch in uint64 type
    function currentEpoch() public view returns(uint64) {
        return uint64((block.timestamp - VOTECYCLE_START) / 2 weeks) + 1;
    }

    /// @notice request withdraw to be eligible for withdrawal after currentEpoch
    /// @dev prior withdrawal request will be overwritten
    /// @param _pid pid to withdraw
    /// @param _amount amount to request withdrawal
    function requestWithdraw(uint256 _pid, uint256 _amount) external {
        require(_amount <= uint256(deposits[_pid][msg.sender].amount), "too much");
        withdrawRequest[_pid][msg.sender] = WithdrawRequest({
            epoch : currentEpoch(),
            amount : uint192(_amount)
        });
    }
}
